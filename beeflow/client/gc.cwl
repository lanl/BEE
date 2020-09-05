# -*- mode: YAML; -*-

class: Workflow
cwlVersion: v1.0

inputs:
  pattern: string
  infile: File

outputs:
  grep_file:
    type: File
    outputSource: grep/outfile
  count_file:
    type: File
    outputSource: wc/outfile

steps:
  grep:
    run:
      class: CommandLineTool
      inputs:
        pattern:
          type: string
          default: "integer"
          inputBinding: {position: 0}
        infile:
          type: File
          default: lorem.txt
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: grepout.txt
      baseCommand: "sleep 15; grep integer lorem.txt > grepout.txt"
      hints:
        DockerRequirement:
          dockerImageId: "/usr/projects/beedev/toss-tiny-3-5.tar"
    in:
      pattern: pattern
      infile: infile
    out: [outfile]

  wc:
    run:
      class: CommandLineTool
      inputs:
        infile:
          type: File
          default: grepout.txt
          inputBinding: {position: 1}
      outputs:
        outfile: stdout
      stdout: counts.txt
      baseCommand: "sleep 10; wc -l grepout.txt > counts.txt"
      hints:
        DockerRequirement:
          dockerImageId: "/usr/projects/beedev/toss-tiny-3-5.tar"
    in:
      infile: grep/outfile
    out: [outfile]
