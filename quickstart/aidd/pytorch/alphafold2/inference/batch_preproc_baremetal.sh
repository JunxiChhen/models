# Copyright (c) 2022 Intel Corporation
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

root_home=$1 # e.g. /home/<your-username>, root path that holds all intermediate IO data
data_dir=$2 # e.g. $root_home/af2data, path that holds all reference database and model params, including mgnify uniref etc.
input_dir=$3 # e.g. $root_home/samples, path of all query .fa files (sequences in fasta format)
out_dir=$4 # e.g. $root_home/experiments, path that contains intermediates output of preprocessing, model inference, and final result

suffix=".fa"
log_dir=$root_home/logs
n_sample=`ls ${input_dir}|grep ${suffix}|wc -l`
n_core=`lscpu|grep "^Core(s) per socket"|awk '{split($0,a," "); print a[4]}'`
n_socket=`lscpu|grep "^Socket(s)"|awk '{split($0,a," "); print a[2]}'`
((n_sample_0=$n_sample-1))
((core_per_instance=$n_core*$n_socket/$n_sample))
script="python run_preprocess.py"
workdir=`pwd`
if [ ! -f "run_preprocess.py" ]; then
  cd $(dirname $0)/../../../../../models/aidd/pytorch/alphafold2/inference
fi

i=0
for f in `ls ${input_dir} | grep ${suffix}`; do
  fpath=${input_dir}/${f}
	((lo=$i*$core_per_instance))
	((hi=($i+1)*$core_per_instance-1))
  ((m=$i/(${n_sample}/2)))
	((ncpu=$core_per_instance))
  echo preprocessing ${fpath} on core $lo to $hi of socket $m
	
	numactl -C $lo-$hi -m $m $script \
		--fasta_paths ${fpath} \
		--output_dir ${out_dir} \
		--bfd_database_path=${data_dir}/bfd/bfd_metaclust_clu_complete_id30_c90_final_seq.sorted_opt \
		--model_names=model_1 \
		--uniclust30_database_path=${data_dir}/uniclust30/uniclust30_2018_08/uniclust30_2018_08 \
		--uniref90_database_path=${data_dir}/uniref90/uniref90.fasta \
		--mgnify_database_path=${data_dir}/mgnify/mgy_clusters_2018_12.fa \
		--pdb70_database_path=${data_dir}/pdb70/pdb70 \
		--template_mmcif_dir=${data_dir}/pdb_mmcif/mmcif_files \
		--data_dir=${data_dir} \
		--max_template_date=2020-05-14 \
		--obsolete_pdbs_path=${data_dir}/pdb_mmcif/obsolete.dat \
		--hhblits_binary_path=`which hhblits` \
		--hhsearch_binary_path=`which hhsearch` \
		--jackhmmer_binary_path=`which jackhmmer` \
		--kalign_binary_path=`which kalign` \
		> ${log_dir}/${f}.txt 2>&1 &
	((i=${i}+1))
done

### wait until done
while true; do
  if [ `ls ${out_dir}|grep timmer|wc -l` -gt 1 ]; then
    n=0
		for f in `ls ${out_dir}|grep timmer`; do
		  status=`cat ${out_dir}/${f}|grep datapipeline|wc -l`
			if [[ $status == 1 ]]; then
			  ((n+=1))
			fi
		done
  else
    n=0
  fi
  if [ $n -eq $n_sample ]; then
    break
  fi
  sleep 60
done
echo "iaf2_preproc_done"
cd $workdir
