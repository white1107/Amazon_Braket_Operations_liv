import boto3
from boto3.session import Session
from collections import defaultdict

class Amazon_Braket_lib:
    def __init__(self,region,clientToken):
        self.region = region
        self.clientToken = clientToken
        braket = boto3.client('braket',region_name=self.region)

    # Example
    # device_a = 'qpu'
    # device_m = 'rigetti'
    # device_e = 'Aspen-10'
    def day_sum_devied_with_backet_counts_device_id(self,device_a,device_m,device_e):

        s3bucket_name_array = []
        s3bucket_dic_name_dic = defaultdict(list)
        s3bucket_dic_id_dic = defaultdict(list)
        count_dic = {}
        count_id = {}

        total_shots = 0
        target_name = ['QUEUED','CANCELLED','COMPLETED']
        target_status = target_name[1]
        #target_status = 'RUNNING'
        device_n = 'device'
        # device_a = 'qpu'
        # device_m = 'rigetti'
        # device_e = 'Aspen-10'
        device_name = device_n+'/'+device_a+'/'+device_m+'/'+device_e


        #Search Quantum Tasks recursively
        next_token = ''

        own_filters = [
            {
                'name': 'deviceArn',
                'operator': 'EQUAL',
                'values': [
                'arn:aws:braket:::device/qpu/rigetti/Aspen-10'
                ]
            },
        ]

        response = braket.search_quantum_tasks(
            filters=own_filters,
            maxResults=100
        )

        for k in response['quantumTasks']:
            # if k['status'] == target_status and k['createdAt'].date() == datetime.date(year,month,day):
            if k['status'] == target_status:
                total_shots +=  + k['shots']

                tmp_s3_dic_name_array = list(k['outputS3Directory'].split('/'))
                if k['outputS3Bucket'] not in s3bucket_name_array:
                    s3bucket_name_array.append(k['outputS3Bucket'])
                    count_dic[k['outputS3Bucket']] = 0
                    count_id[k['outputS3Bucket']] = []
                count_dic[k['outputS3Bucket']] += k['shots']
                count_id[k['outputS3Bucket']].append(k['quantumTaskArn'])

                if tmp_s3_dic_name_array[0] not in s3bucket_dic_name_dic[k['outputS3Bucket']]:
                    s3bucket_dic_name_dic[k['outputS3Bucket']].append(tmp_s3_dic_name_array[0])
                    count_dic[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]] = 0
                    count_id[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]] = []
                count_dic[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]] += k['shots']
                count_id[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]].append(k['quantumTaskArn'])

        if 'nextToken' in response:next_token = response['nextToken']
        else:next_token = False

        while next_token:
            response = braket.search_quantum_tasks(
                filters=own_filters,
                maxResults=100,
                nextToken = next_token
            )
            for k in response['quantumTasks']:
                # if k['status'] == target_status and k['createdAt'].date() == datetime.date(year,month,day):

                if k['status'] == target_status:
                    total_shots +=  + k['shots']

                    tmp_s3_dic_name_array = list(k['outputS3Directory'].split('/'))
                    if k['outputS3Bucket'] not in s3bucket_name_array:
                        s3bucket_name_array.append(k['outputS3Bucket'])
                        count_dic[k['outputS3Bucket']] = 0
                    count_dic[k['outputS3Bucket']] += k['shots']
                    if tmp_s3_dic_name_array[0] not in s3bucket_dic_name_dic[k['outputS3Bucket']]:
                        s3bucket_dic_name_dic[k['outputS3Bucket']].append(tmp_s3_dic_name_array[0])
                        count_dic[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]] = 0
                    count_dic[k['outputS3Bucket']+'/'+tmp_s3_dic_name_array[0]] += k['shots']

            if 'nextToken' in response:next_token = response['nextToken']
            else:break

        return count_id,count_dic

    def delete_quantumTask(self,quantumTaskArn_name):
        response = braket.cancel_quantum_task(clientToken= self.clientToken, quantumTaskArn= quantumTaskArn_name)
        return response