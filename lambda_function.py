import boto3
import datetime

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    today = datetime.datetime.utcnow()
    date_str = today.strftime('%Y-%m-%d')

    ## -------- EC2 AMI BACKUPS -------- ##
    instances = ec2.describe_instances()

    for reservation in instances['Reservations']:
        for instance in reservation['Instances']:
            instance_id = instance['InstanceId']
            state = instance['State']['Name']
            root_device_name = instance.get('RootDeviceName')
            block_devices = instance.get('BlockDeviceMappings', [])
            root_device_type = instance.get('RootDeviceType')

            # Log instance metadata
            print(f"\nChecking instance {instance_id}")
            print(f"State: {state}")
            print(f"RootDeviceName: {root_device_name}")
            print(f"RootDeviceType: {root_device_type}")
            print(f"BlockDeviceMappings: {block_devices}")

            # Skip if not running or stopped
            if state not in ['running', 'stopped']:
                print(f"Skipping {instance_id} - Instance not in a valid state.")
                continue

            # Skip if not EBS-backed
            if root_device_type != 'ebs':
                print(f"Skipping {instance_id} - Not EBS-backed.")
                continue

            # Skip if no valid root volume attached
            root_device_attached = any(
                bdm.get('DeviceName') == root_device_name for bdm in block_devices
            )
            if not root_device_name or not root_device_attached:
                print(f"Skipping {instance_id} - No valid root device mapping.")
                continue

            # Get instance Name tag
            name = ''
            for tag in instance.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']

            ami_name = f"Backup-{name or instance_id}-{date_str}"
            print(f"Creating AMI for {instance_id} with name {ami_name}")

            try:
                ec2.create_image(
                    InstanceId=instance_id,
                    Name=ami_name,
                    NoReboot=True
                )
            except Exception as e:
                print(f"Error creating AMI for {instance_id}: {e}")
                continue

    ## -------- EBS SNAPSHOTS -------- ##
    volumes = ec2.describe_volumes()

    for volume in volumes['Volumes']:
        volume_id = volume['VolumeId']
        snapshot_description = f"Snapshot-{volume_id}-{date_str}"
        print(f"Creating snapshot for volume {volume_id}")

        try:
            ec2.create_snapshot(
                VolumeId=volume_id,
                Description=snapshot_description,
                TagSpecifications=[
                    {
                        'ResourceType': 'snapshot',
                        'Tags': [{'Key': 'Name', 'Value': snapshot_description}]
                    }
                ]
            )
        except Exception as e:
            print(f"Error creating snapshot for volume {volume_id}: {e}")
            continue

    return {
        'statusCode': 200,
        'body': 'AMI and EBS backups completed with validations.'
    }
