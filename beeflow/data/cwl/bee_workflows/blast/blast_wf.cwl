# -*- mode: YAML; -*-

class: Workflow
cwlVersion: v1.2

inputs:
  ### blast_split ###
  input_file: File
  query_granularity: int
  ### blast_worker001 ###
  program_name: string
  database: string
  worker001_output: string
  ### blast_worker002 ###
  worker002_output: string
  ### blast_output ###
  cat_output: string


outputs:
  blast_output:
    type: File
    outputSource: blast_output/blast_output
  blast_output_err:
    type: File
    outputSource: blast_output_err/blast_output_err

steps:
  blast_split:
    run: blast_split.cwl
    in:
      input_file: input_file
      query_granularity: query_granularity
    out: [split1, split2]
    hints:
      DockerRequirement:
        beeflow:useContainer: "/usr/projects/beedev/blast-example.tar.gz"

  blast_worker001:
    run: blast_worker001.cwl
    in:
      program_name: program_name
      database: database
      input_file: blast_split/split1
      output_file: worker001_output
    out: [output, output_err]
    hints:
      DockerRequirement:
        beeflow:useContainer: "/usr/projects/beedev/blast-example.tar.gz"

  blast_worker002:
    run: blast_worker002.cwl
    in:
      program_name: program_name
      database: database
      input_file: blast_split/split2
      output_file: worker002_output
    out: [output, output_err]
    hints:
      DockerRequirement:
        beeflow:useContainer: "/usr/projects/beedev/blast-example.tar.gz"

  blast_output:
    run: blast_output.cwl
    in:
      input_file1: blast_worker001/output
      input_file2: blast_worker002/output
      output_filename: cat_output
    out: [blast_output]
    hints:
      DockerRequirement:
        beeflow:useContainer: "/usr/projects/beedev/blast-example.tar.gz"

  blast_output_err:
    run: blast_output_err.cwl
    in:
      input_file1: blast_worker001/output_err
      input_file2: blast_worker002/output_err
    out: [blast_output_err]
    hints:
      DockerRequirement:
        beeflow:useContainer: "/usr/projects/beedev/blast-example.tar.gz"

