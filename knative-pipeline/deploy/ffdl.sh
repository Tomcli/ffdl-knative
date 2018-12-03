sed -i s/s3_endpoint_url/$s3_endpoint_url/ $manifest
sed -i s/s3_access_key_id/$s3_access_key_id/ $manifest
sed -i s/s3_secret_access_key/$s3_secret_access_key/ $manifest
echo $(curl -H "accept: application/json" -H "Authorization: test" -H "X-Watson-Userinfo: bluemix-instance-id=test-user" -X POST $ffdlrest/v1/models?version=2017-02-13 -F "model_definition=@$modelfile" -F "manifest=@$manifest") | jq ".model_id" | tr -d '"' > /tmp/training-id.txt;
export id=$(cat /tmp/training-id.txt);
while [ "$status" != "COMPLETED" ]
do
  export status=$(echo $(curl -X GET "$ffdlrest/v1/models/$id?version=2017-02-13" -H "accept: application/json" -H "X-Watson-Userinfo: bluemix-instance-id=test-user" -H "Authorization: test") | jq ".training.training_status.status" | tr -d '"');
  sleep 5s;
done
