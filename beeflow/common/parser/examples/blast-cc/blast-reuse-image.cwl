cwlVersion: v1.0
class: Workflow

requirements:
  InlineJavascriptRequirement: {}
  StepInputExpressionRequirement: {}

id: blast_flow
label: blast-flow

inputs:
  dir: string
  tarball: string
  scripts_dir: string?
  split_script: string
  worker_script: string
  output_script: string
  output_err_script: string
  output_dir: string?
  worker0: string 
  worker1: string

outputs: []

steps:

  ch_tar2dir:
    in:
      dir: dir
      tarball: tarball

    out: 
      [image] 
    run: ./ch-donttar2dir.cwl

  blast_split:
    in:
      scripts_dir: scripts_dir
      output_dir: output_dir
      image: ch_tar2dir/image
      split_script: split_script
      system:
        default: '--'
      cc_flags:
        default: '--no-home'
    out:
      [split_done]
    run: ./blast-split.cwl

  blast_worker0:
    in:
      scripts_dir: scripts_dir
      output_dir: output_dir
      split_done: blast_split/split_done
      image: ch_tar2dir/image
      worker_script: worker_script 
      system:
        default: '--'
      cc_flags:
        default: '--no-home'
      worker0: worker0
    out:
      [worker0_done]
    run: ./blast-worker0.cwl

  blast_worker1:
    in:
      scripts_dir: scripts_dir
      output_dir: output_dir
      split_done: blast_split/split_done
      image: ch_tar2dir/image
      worker_script: worker_script 
      system:
        default: '--'
      cc_flags:
        default: '--no-home'
      worker1: worker1
    out:
      [worker1_done]
    run: ./blast-worker1.cwl

  blast_output:
    in:
      scripts_dir: scripts_dir
      output_dir: output_dir
      image: ch_tar2dir/image
      output_script: output_script 
      system:
        default: '--'
      cc_flags:
        default: '--no-home'
      worker0_done: blast_worker0/worker0_done
      worker1_done: blast_worker1/worker1_done
    out: 
      [output_done]
    run: ./blast-output.cwl

  blast_output_err:
    in:
      scripts_dir: scripts_dir
      output_dir: output_dir
      image: ch_tar2dir/image
      output_err_script: output_err_script 
      system:
        default: '--'
      cc_flags:
        default: '--no-home'
      worker0_done: blast_worker0/worker0_done
      worker1_done: blast_worker1/worker1_done
    out: 
      [output_err_done]
    run: ./blast-output-err.cwl

#  ch_remove:
#    in:
#      image: ch_tar2dir/image
#      rm_flags:
#        default: '-rf'
#      output_done: blast_output/output_done
#      output_err_done: blast_output_err/output_err_done
#    out: []
#    run: ./ch-remove.cwl

