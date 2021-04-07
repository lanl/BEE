# -*- mode: YAML; -*-

class: Workflow
cwlVersion: v1.0

inputs:
  sequence_file: File

outputs: []

steps:
  makeblastdb:
    run:
      class: CommandLineTool
      baseCommand: "makeblastdb -in reference.fasta -title reference -dbtype nucl -out databases/reference"
      hints:
        DockerRequirement:
          # This must be the container location on the system to be run
          dockerImageId: "/home/cc/blast.tar.gz"
      inputs:
        sequence_file:
          type: string
      outputs:
        db_dir:
          type: string
    in:
      sequence_file: sequence_file
    out: [db_dir]

  worker0:
    run:
      class: CommandLineTool
      baseCommand: "blastn -db databases/reference -query sequences.fasta -evalue 1e-3 -word_size 11 -outfmt 0 > worker0.reference"
      hints:
        DockerRequirement:
          dockerImageId: "/home/cc/blast.tar.gz"
      inputs:
        db_dir:
          type: string
      outputs:
        out:
          type: string
    in:
      db_dir: makeblastdb/db_dir
    out: [out]

  worker1:
    run:
      class: CommandLineTool
      # TODO: Modify command options
      baseCommand: "blastn -db databases/reference -query sequences.fasta -evalue 1e-3 -word_size 20 -outfmt 0 > worker1.reference"
      hints:
        DockerRequirement:
          dockerImageId: "/home/cc/blast.tar.gz"
      inputs:
        db_dir:
          type: string
      outputs:
        out:
          type: string
    in:
      db_dir: makeblastdb/db_dir
    out: [out]
