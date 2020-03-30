# Submit the request 
# Returns the id
id=$(curl -i -H "Content-Type: application/json" -X POST -d  '{"title":"Bam"}' http://127.0.0.1:5000/bee_orc/v1/jobs/)

echo "The id is $id"

# Submit the workflow 
curl -i -H "Content-Type: application/json" -X POST -F 'workflow=@workflow.cwl'  http://127.0.0.1:5000/bee_orc/v1/jobs/42
