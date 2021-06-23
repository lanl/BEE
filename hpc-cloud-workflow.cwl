# Test workflow for HPC+Cloud affinity
class: Workflow
cwlVersion: v1.0
inputs: {input0: File}
outputs: []
steps:
  hpc-task1:
    in: {input: input0}
    out: [out]
    run:
      class: CommandLineTool
      baseCommand: sleep 10
      hints:
        Affinity: {resource: HPC}
      inputs:
        input: {type: string}
      outputs:
        output: {type: string}
  hpc-task2:
    in: {input: hpc-task1/out}
    out: [out]
    run:
      class: CommandLineTool
      baseCommand: sleep 20
      hints:
        Affinity: {resource: HPC}
      inputs:
        input: {type: string}
      outputs:
        out: {type: string}
  cloud-task1:
    in: {input: input0}
    out: [out]
    run:
      class: CommandLineTool
      baseCommand: sleep 20
      hints:
        Affinity: {resource: CLOUD}
      inputs:
        input: {type: string}
      outputs:
        out: {type: string}
  cloud-task2:
    in: {input: cloud-task1/out}
    out: [out]
    run:
      class: CommandLineTool
      baseCommand: sleep 16
      hints:
        Affinity: {resource: CLOUD}
      inputs:
        input: {type: string}
      outputs:
        out: {type: string}
