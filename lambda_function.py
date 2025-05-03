import boto3                          # Import AWS SDK to interact with AWS services
import datetime                      # Import for handling date and time

ec2 = boto3.client('ec2')           # Create a low-level EC2 client

def lambda_handler(event, context):                        # Lambda entry point
    today = datetime.datetime.utcnow()                    # Get current UTC datetime
    date_str = today.strftime('%Y-%m-%d')                 # Format date like '2025-05-01'

    ## -------- EC2 AMI BACKUPS -------- ##
    instances = ec2.describe_instances()                  # Get all EC2 instances

    for reservation in instances['Reservations']:         # Loop over each reservation (group of instances)
        for instance in reservation['Instances']:         # Loop over each instance inside a reservation

            instance_id = instance['InstanceId']                              # Extract instance ID
            state = instance['State']['Name']                                 # Get the state (running/stopped/etc.)
            root_device_name = instance.get('RootDeviceName')                 # e.g., /dev/sda1 (boot volume path)
            block_devices = instance.get('BlockDeviceMappings', [])           # All attached volumes
            root_device_type = instance.get('RootDeviceType')                 # 'ebs' or 'instance-store'

            # Logging for debug
            print(f"\nChecking instance {instance_id}")
            print(f"State: {state}")
            print(f"RootDeviceName: {root_device_name}")
            print(f"RootDeviceType: {root_device_type}")
            print(f"BlockDeviceMappings: {block_devices}")

            # -- CHECK 1: VALID INSTANCE STATE --
            if state not in ['running', 'stopped']:                         # Only backup if instance is active or stopped
                print(f"Skipping {instance_id} - Invalid state.")
                continue                                                    # Skip to next instance

            # -- CHECK 2: INSTANCE MUST BE EBS-BACKED --
            if root_device_type != 'ebs':                                   # If instance is instance-store, skip
                print(f"Skipping {instance_id} - Not EBS-backed.")
                continue

            # -- CHECK 3: ROOT DEVICE MUST BE ATTACHED --
            root_device_attached = any(                                     # Check if root device is present in volumes
                bdm.get('DeviceName') == root_device_name
                for bdm in block_devices
            )
            if not root_device_name or not root_device_attached:
                print(f"Skipping {instance_id} - No root volume attached.")
                continue

            # -- GET INSTANCE NAME FROM TAGS --
            name = ''                                                       # Default name if no tag found
            for tag in instance.get('Tags', []):                            # Search for Name tag
                if tag['Key'] == 'Name':
                    name = tag['Value']                                     # Extract tag value

            ami_name = f"Backup-{name or instance_id}-{date_str}"          # Construct AMI name
            print(f"Creating AMI for {instance_id} as {ami_name}")

            try:
                ec2.create_image(                                           # Call AWS API to create AMI
                    InstanceId=instance_id,
                    Name=ami_name,
                    NoReboot=True                                          # Avoid rebooting the instance
                )
            except Exception as e:
                print(f"Error creating AMI for {instance_id}: {e}")         # Catch and log errors
                continue

    ## -------- EBS SNAPSHOTS -------- ##
    volumes = ec2.describe_volumes()                                       # Get all volumes in region

    for volume in volumes['Volumes']:                                      # Loop over each volume
        volume_id = volume['VolumeId']                                     # Get Volume ID
        snapshot_description = f"Snapshot-{volume_id}-{date_str}"         # Description for snapshot
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

