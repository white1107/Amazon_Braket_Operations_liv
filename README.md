# ライブラリまとめ

## この設計にした理由：

1. タスクを投げたユーザーの特定は不可
2. しかし、タスク結果を保存するS3の情報取得はできたため、その情報を元に操作する。
3. 他人が作成した、タスクも削除することができる。

# AWS Braket

### search_quantum_tasksの使用例

## 1. 特定のstatus,regionタスクの総合shot数全て取得する

```python
from boto3.session import Session

braket = boto3.client('braket',region_name='us-west-1')

total_shots = 0
target_status = 'CANCELLED'

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
    if k['status'] == target_status:
        print('Shots is :' + str(k['shots']))
        total_shots +=  + k['shots']

if 'nextToken' in response:next_token = response['nextToken']
else:next_token = False

while next_token:
    response = braket.search_quantum_tasks(
        filters=own_filters,
        maxResults=100,
        nextToken = next_token
    )
    for k in response['quantumTasks']:
        if k['status'] == target_status:
            print('Shots is :' + str(k['shots']))
            total_shots +=  + k['shots']
    if 'nextToken' in response:next_token = response['nextToken']
    else:break

print('Total Shots for ' + target_status + ' tasks is :' + str(total_shots))
```

## 2. 特定のstatus,regionタスクを全て取得して、S3のレポジトリ別に表示、同時にtask ID を返す。

return 

type : dictionary 

```python
import boto3
from boto3.session import Session
from collections import defaultdict

braket = boto3.client('braket',region_name='us-west-1')

# Example
# device_a = 'qpu'
# device_m = 'rigetti'
# device_e = 'Aspen-10'

def day_sum_devied_with_backet_counts_device_id(device_a,device_m,device_e):
    
    s3bucket_name_array = []
    s3bucket_dic_name_dic = defaultdict(list)
    s3bucket_dic_id_dic = defaultdict(list)
    count_dic = {}
    count_id = {}
    
    
    total_shots = 0
    target_name = ['QUEUED','CANCELLED','COMPLETED']
    target_status = target_name[1]
    device_n = 'device'
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
    print('Status is :', target_status)
    print('device info :', device_name)
    print(count_dic)
    return count_id,count_dic
```

## 3. IDを取得してQUE に入ってるTaskを削除する

user token はアカウント作成した時にダウンロードしたCSVに掲載してある。

tokenを入れて毎回の入力を省略した。

```python
def delete_quantumTask(quantumTaskArn_name):
    response = braket.cancel_quantum_task(clientToken= 'USER_TOKEN', quantumTaskArn= quantumTaskArn_name)
    return response
```

## 2,3 を組み合わせて特定のS3レポジトリのタスクを削除する

```python
count_id,count_dic = day_sum_devied_with_backet_counts_device_id('qpu','rigetti','Aspen-10')
```

outputs

```python
Status is : CANCELLED
device info : device/qpu/rigetti/Aspen-10
{'amazon-braket-masumoto': 120, 'amazon-braket-masumoto/Sandbox': 10, 'amazon-braket-masumoto/Your-Folder-Name': 110}
```

example : delete 'amazon-braket-masumoto/Sandbox'

```python
repository = amazon-braket-masumoto/Sandbox
for task_id in count_id[repository]:
	delete_quantumTask(task_id)
```

---

元にしたライブラリ

## cancel_quantum_taks(**kwargs)

**Request Syntax**

```python
response **=** client**.**cancel_quantum_task(
    clientToken**=**'string',
    quantumTaskArn**=**'string'
```

**Response Syntax**

```python

response = client**.**cancel_quantum_task(
    clientToken='string',
    quantumTaskArn='string'
)
```

[Braket - Boto3 Docs 1.20.16 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/braket.html#Braket.Client.cancel_quantum_task)

## search_quantum_tasks(**kwargs)

**Request Syntax**

```python
response **=** client**.**search_quantum_tasks(
    filters**=**[
        {
            'name': 'string',
            'operator': 'LT'**|**'LTE'**|**'EQUAL'**|**'GT'**|**'GTE'**|**'BETWEEN',
            'values': [
                'string'
            ]
        },
    ],
    maxResults**=**123,
    nextToken**=**'string'
)
```

**Response Syntax**

```python
`{
    'nextToken': 'string',
    'quantumTasks': [
        {
            'createdAt': datetime(2015, 1, 1),
            'deviceArn': 'string',
            'endedAt': datetime(2015, 1, 1),
            'outputS3Bucket': 'string',
            'outputS3Directory': 'string',
            'quantumTaskArn': 'string',
            'shots': 123,
            'status': 'CREATED'**|**'QUEUED'**|**'RUNNING'**|**'COMPLETED'**|**'FAILED'**|**'CANCELLING'**|**'CANCELLED',
            'tags': {
                'string': 'string'
            }
        },
    ]
}`
```

[Braket - Boto3 Docs 1.20.16 documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/braket.html#Braket.Client.search_quantum_tasks)