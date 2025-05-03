# 🛡️ Project: Automated EC2 AMI & EBS Snapshot Backups Using AWS Lambda

---

### 📌 **Overview**

This project automates:

* **EC2 AMI image creation** for all EC2 instances
* **EBS volume snapshot creation** for all attached volumes

The process is triggered via an **Amazon CloudWatch Event Rule**, and executed through an **AWS Lambda function** written in Python. It ensures all running EC2 instances and EBS volumes are backed up, avoiding redundant or failed backups.

---

## 🎯 Objective

To build a **serverless, automated backup system** that:

* Creates **AMI backups** of all EC2 instances daily.
* Creates **snapshots** of all EBS volumes.
* Tags each backup with a consistent naming scheme and date.
* Handles errors gracefully and avoids duplicate AMI names.
* Requires **no manual intervention** after deployment.

---

### 🏗️ **Architecture**

```text
+----------------------------+
|  CloudWatch Event Rule    |   ← Trigger: Scheduled (e.g., daily at 2 AM UTC)
+-------------+--------------+
              |
              v
+----------------------------------+
|  Lambda Function (Python)        |
|  - Creates AMIs for instances    |
|  - Creates EBS Snapshots         |
+----------------------------------+
              |
              v
+----------------------------+
|    AWS EC2 & EBS APIs     |
+----------------------------+
```

---


## 🔁 Workflow

1. **EventBridge Trigger** fires Lambda on a schedule.
2. **Lambda Function** fetches all EC2 instances and volumes.
3. For each valid EC2 instance:

   * Confirm EBS-backed root volume.
   * Create an AMI: `Backup-<instance-name>-<date>`.
4. For each EBS volume:

   * Create a snapshot and tag with `Name` and date.
5. **CloudWatch Logs** record all operations and errors.

---

### 🖼️ AWS Console Screenshots


 #### IAM Role & Permissions    
 <img width="1470" alt="Screenshot 2025-05-03 at 10 57 14 AM" src="https://github.com/user-attachments/assets/b3d55273-171e-4486-ba5c-51d799582239" />


#### Lambda Function Setup      
<img width="1470" alt="Screenshot 2025-05-03 at 11 00 56 AM" src="https://github.com/user-attachments/assets/62f5a658-57f7-475b-89e5-66e030cf8a6b" />
<img width="1470" alt="Screenshot 2025-05-02 at 3 55 55 PM" src="https://github.com/user-attachments/assets/37ef290b-20ea-45a2-b61d-28124f2f11c8" />

#### CloudWatch Event Rule     
<img width="1470" alt="Screenshot 2025-05-03 at 11 03 19 AM" src="https://github.com/user-attachments/assets/8eb31e5f-f2d7-422a-a6ec-88077d222a7b" />

#### EC2 Console (Before/After)   
<img width="1470" alt="Screenshot 2025-05-02 at 3 48 37 PM" src="https://github.com/user-attachments/assets/08399b63-7a60-4722-ad27-63d7d3888faa" />
<img width="1470" alt="Screenshot 2025-05-02 at 3 49 09 PM" src="https://github.com/user-attachments/assets/ddb9f726-7a00-4ac8-b52b-b7fb32d9c956" />


---

## 🔐 IAM Role Permissions for Lambda

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:CreateImage",
        "ec2:CreateSnapshot",
        "ec2:CreateTags"
      ],
      "Resource": "*"
    }
  ]
}
```

---

## 🔧 Problems Faced During Development

| ❗ **Problem**                              | 📋 **Cause**                                             | 💡 **Solution**                                                                         |
| ------------------------------------------ | -------------------------------------------------------- | --------------------------------------------------------------------------------------- |
| `InvalidParameterValue` - No root volume   | Instance had no valid root or was instance-store backed  | Added validation for `RootDeviceType`, `RootDeviceName`, and `BlockDeviceMappings`      |
| `InvalidAMIName.Duplicate` error           | AMI names must be globally unique within region          | Used `datetime` to append today’s date in the AMI name to ensure uniqueness             |
| Function halted on single instance failure | Exceptions during image/snapshot creation were unhandled | Wrapped logic in `try-except` blocks to log and skip failures without stopping the flow |
| Missing logs and visibility                | Skipped resources were not logged                        | Added `print()` logs visible in CloudWatch for all decisions and errors                 |

---

### ✅ **Key Takeaways**

* Scheduled automation using CloudWatch + Lambda is efficient and serverless.
* Backup reliability improves by waiting for the correct EC2 state.
* IAM permissions must be precisely granted.
* Error handling and retry logic are essential for real-world reliability.

---



