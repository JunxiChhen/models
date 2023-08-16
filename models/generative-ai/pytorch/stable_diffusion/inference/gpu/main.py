#!/usr/bin/env bash
#
# Copyright (c) 2023 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import time
import sys
import torch
from diffusers import StableDiffusionPipeline
import argparse
import numpy as np
from scipy.linalg import sqrtm
from PIL import Image
import pytorch_fid

parser = argparse.ArgumentParser(description='PyTorch StableDiffusion TexttoImage')
parser.add_argument("--arch", type=str, default='CompVis/stable-diffusion-v1-4', help="model name")
parser.add_argument('--prompt', default=[
    "a photo of an astronaut riding a horse on mars", 
    "a photo of a cat skates in Square", 
    "A painting of a squirrel eating a burger",
    "A photo of dog in the room"], type=list, help='prompt')
parser.add_argument('--batch_size', default=1, type=int, help='batch size')
parser.add_argument('--idx_start', default=0, type=int, help='select the start index of image')
parser.add_argument('--precision', default="fp32", type=str, help='precision')
parser.add_argument('--amp', action='store_true', default=False, help='use amp in model')
parser.add_argument('--jit', action='store_true', default=False, help='enable JIT')
parser.add_argument('--iteration', default=5, type=int, help='test iterations')
parser.add_argument('--warmup_iter', default=2, type=int, help='test warmup')
parser.add_argument('--device', default='xpu', type=str, help='cpu, cuda or xpu')
parser.add_argument('--save_image', action='store_true', default=False, help='save image')
parser.add_argument('--save_tensor', action='store_true', default=False, help='save tensor')
parser.add_argument('--accuracy', action='store_true', default=False, help='compare the result with cuda')
parser.add_argument('--wei_path', default='CompVis/stable-diffusion-v1-4', type=str, metavar='PATH',
                    help='path to model structure or weight')
parser.add_argument('--ref_path', default='', type=str, metavar='PATH',
                    help='path to reference image (default: none)')
parser.add_argument('--save_path', default='./xpu_result', type=str, help='output image dir')
parser.add_argument('--num_inference_steps', default=50, type=int, help='number of unet step')
parser.add_argument('--channels_last', action='store_true', default=False, help='use channels last in inference')
args = parser.parse_args()
print(args)

def compare(xpu_res, ref_res):
    xpu = torch.tensor(xpu_res) 
    ref = torch.tensor(ref_res) 
    
    diff_value = torch.abs((xpu - ref))
    max_diff = torch.max(diff_value)

    shape = 1
    for i in range(xpu.dim()):
        shape = shape * xpu.shape[i]

    value = diff_value > 0.1
    num = torch.sum(value.contiguous().view(-1))
    ratio1 = num / shape
    print("difference larger than 0.1, ratio = {}".format(ratio1))  
  
    value = diff_value > 0.01 
    num = torch.sum(value.contiguous().view(-1))
    ratio2 = num / shape
    print("difference larger than 0.01, ratio = {}".format(ratio2))  

    value = diff_value > 0.001 
    num = torch.sum(value.contiguous().view(-1))
    ratio3 = num / shape
    print("difference larger than 0.001, ratio = {}".format(ratio3))  

    if ratio1 < 0.01 and ratio2 < 0.08 and ratio3 < 0.4:
        print("accuracy pass")
    else:
        print("accuracy fail")
        
def compare_pil_images(ref_res, cur_res):
    xpu = torch.tensor(np.array(cur_res)) 
    ref = torch.tensor(np.array(ref_res)) 
    
    diff_value = torch.abs((xpu - ref))
    max_diff = torch.max(diff_value)

    shape = 1
    for i in range(xpu.dim()):
        shape = shape * xpu.shape[i]

    value = diff_value > 0.1
    num = torch.sum(value.contiguous().view(-1))
    ratio1 = num / shape
    print("difference larger than 0.1, ratio = {}".format(ratio1))  
  
    value = diff_value > 0.01 
    num = torch.sum(value.contiguous().view(-1))
    ratio2 = num / shape
    print("difference larger than 0.01, ratio = {}".format(ratio2))  

    value = diff_value > 0.001 
    num = torch.sum(value.contiguous().view(-1))
    ratio3 = num / shape
    print("difference larger than 0.001, ratio = {}".format(ratio3))  

    if ratio1 < 0.01 and ratio2 < 0.08 and ratio3 < 0.4:
        print("accuracy pass")
    else:
        print("accuracy fail")

def main():
    profiling = os.environ.get("PROFILE", "OFF").upper() in ["1", "Y", "ON", "YES", "TRUE"]

    # prompt = ["A painting of a squirrel eating a burger"]
    seed = 666
    if args.device == "xpu":
        import intel_extension_for_pytorch as ipex
        idx = torch.xpu.current_device()
        generator = torch.xpu.default_generators[idx]
        generator.manual_seed(seed)
    elif args.device == "cuda":
        generator = torch.Generator(device=args.device).manual_seed(seed)
    else:
        generator = torch.Generator(device=args.device)

    if args.precision == "fp32":
        datatype = torch.float
    elif args.precision == "fp16":
        datatype = torch.float16
    elif args.precision == "bf16":
        datatype = torch.bfloat16
    else:
        print("unsupported datatype")
        sys.exit()

    if args.precision == "fp32":
        pipe = StableDiffusionPipeline.from_pretrained(args.wei_path)
    else:
        pipe = StableDiffusionPipeline.from_pretrained(args.wei_path, torch_dtype=datatype, revision=args.precision)
    if args.channels_last:
        pipe.unet = pipe.unet.to(memory_format=torch.channels_last)
        pipe.vae.to(memory_format=torch.channels_last)
        print("---- Use NHWC model.")

    pipe = pipe.to(args.device)
    if args.amp:
        pipe.unet = torch.xpu.optimize(model=pipe.unet, dtype=datatype)

    out_type = "pil"
    if args.accuracy or args.save_tensor:
        out_type = "tensor"

    total_time = 0
    print("output type is: ", out_type)
    with torch.no_grad():
        for step in range(args.warmup_iter):
            idx1 = args.idx_start + int(step * args.batch_size)
            idx2 = args.idx_start + int((step + 1) * args.batch_size)
            input = args.prompt[idx1:idx2]
            if args.device == "xpu":
                if args.amp:
                    with torch.xpu.amp.autocast(enabled=True, dtype=datatype):
                        images = pipe(input, generator=generator, num_inference_steps=args.num_inference_steps, output_type=out_type).images
                else:
                    images = pipe(input, generator=generator, num_inference_steps=args.num_inference_steps, output_type=out_type).images
                torch.xpu.synchronize()
            elif args.device == "cuda":
                images = pipe(input, generator=generator, num_inference_steps=args.num_inference_steps, output_type=out_type).images
                torch.cuda.synchronize()
            else:
                images = pipe(input, generator=generator, num_inference_steps=args.num_inference_steps, output_type=out_type).images

        image_before = []
        iter = 0
        for step in range(args.iteration):
            print("Iteration = {}".format(step))
            step = 0
            idx1 = args.idx_start + int(step * args.batch_size)
            idx2 = args.idx_start + int((step + 1) * args.batch_size)
            print("idx1={}".format(idx1))
            print("idx2={}".format(idx2))
            input = args.prompt[idx1:idx2]
            print("input is : ", input)


            if args.device == "xpu":
                with torch.autograd.profiler_legacy.profile(profiling, use_xpu=True, record_shapes=True) as prof:
                    try:
                        import memory_check
                        memory_check.display_mem("xpu:0")
                    except:
                        pass
                    start_time = time.time()
                    if args.amp:
                        with torch.xpu.amp.autocast(enabled=True, dtype=datatype):
                            images = pipe(input, generator=generator, num_inference_steps=args.num_inference_steps, output_type=out_type).images
                    else:
                        images = pipe(input, generator=generator, num_inference_steps=args.num_inference_steps, output_type=out_type).images
                    torch.xpu.synchronize()
                    end_time = time.time()
                if profiling:
                    torch.save(prof.key_averages().table(sort_by="self_xpu_time_total"), 'profile.pt')
                    torch.save(prof.table(sort_by="id", row_limit=-1), 'profile_detailed.pt')
                    prof.export_chrome_trace('./profile_trace.json')
            elif args.device == "cuda":
                start_time = time.time()
                images = pipe(input, generator=generator, num_inference_steps=args.num_inference_steps, output_type=out_type).images
                torch.cuda.synchronize()
                end_time = time.time()
            else:
                start_time = time.time()
                images = pipe(input, generator=generator, num_inference_steps=args.num_inference_steps, output_type=out_type).images
                end_time = time.time()


            iter_time = end_time - start_time
            total_time += iter_time
            # latency = total_time / (step + 1)
            # throughput = args.batch_size / latency
            # print("---latency={} s".format(latency))
            # print("---throughput={} fps".format(throughput))

            if args.accuracy:
                for i in range(args.batch_size):
                    name = "result_{}_{}.png".format(idx1 + i, iter) if args.save_image else "result_{}_{}.pt".format(idx1 + i, iter)
                    name = os.path.join(args.ref_path, name)
                    if args.save_image:
                        ref_image = Image.open(name)
                        compare_pil_images(ref_image, images[i])
                    else:
                        ref_pt = torch.load(name)
                        compare(ref_pt, images[i])

            if not os.path.exists(args.save_path):
                os.mkdir(args.save_path)

            if args.save_tensor:
                for i in range(args.batch_size):
                    file_name = "./result_{}_{}.pt".format(idx1 + i, iter)
                    save_path = os.path.join(args.save_path, file_name)
                    torch.save(images[i], save_path)

            if args.save_image:
                for i in range(args.batch_size):
                    file_name = "./result_{}_{}.png".format(idx1 + i, iter)
                    save_path = os.path.join(args.save_path, file_name)
                    images[i].save(save_path)
            iter += 1

        total_sample = args.iteration * args.batch_size
        latency = total_time / total_sample * 1000
        throughput = total_sample / total_time
        print("inference Latency: {} ms".format(latency))
        print("inference Throughput: {} samples/s".format(throughput))


if __name__ == '__main__':
    main() 
