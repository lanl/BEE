from beeflow.common.BeeCWL.BeeCWL import BeeCWL

p1 = BeeCWL("./echo2-wf.cwl")
result = p1.parser
print(result)

p2 = BeeCWL("./blast-cc/blast-cc-flow.cwl")
result2 = p2.parser
print(result2)