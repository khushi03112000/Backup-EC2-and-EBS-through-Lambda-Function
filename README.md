## 📁 Project Title: **Automated EC2 AMI and EBS Volume Backup Using AWS Lambda (Event-Driven)**

---

### 📌 **Overview**

This project automates:

* **EC2 AMI image creation** for all EC2 instances
* **EBS volume snapshot creation** for all attached volumes

The process is triggered via an **Amazon CloudWatch Event Rule**, and executed through an **AWS Lambda function** written in Python. It ensures all running EC2 instances and EBS volumes are backed up, avoiding redundant or failed backups.

---

### 🎯 **Objective**

* Automatically create **AMI backups** for all EC2 instances.
* Take **EBS snapshots**, but only if no recent snapshot exists.
* Ensure backups only happen when instances are in a `running` state.
* Handle AWS throttling and timing gracefully.

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

### 🔁 **Workflow**

1. **Trigger via CloudWatch**:

   * A scheduled rule (e.g., every day at 2 AM) invokes the Lambda function.

2. **Instance Handling**:

   * Lists all EC2 instances.
   * Waits up to **3 minutes** for each instance to enter the `running` state.
   * If not running within that time, the AMI backup for that instance is **skipped** to prevent failure.

3. **AMI Backup**:

   * Once running, a timestamped AMI is created for the instance using `NoReboot=True`.
   * Instance name (from tags) is used in the AMI name for clarity.

4. **EBS Snapshot Creation**:

   * Lists all EBS volumes.
   * Checks if a snapshot exists within the last **5 minutes**.
   * If no recent snapshot exists, creates one and tags it accordingly.

5. **API Throttling**:

   * Uses `time.sleep(2)` between snapshot requests to avoid `SnapshotCreationPerVolumeRateExceeded` errors.

---

### 🖼️ **Where to Add AWS Console Screenshots**

| Section                    | Screenshot To Capture                                                   |
| -------------------------- | ----------------------------------------------------------------------- |
| IAM Role & Permissions     | Role attached to Lambda and inline policy with EC2/EBS actions          |
| Lambda Function Setup      | Lambda console with Python code and increased timeout (e.g., 5 minutes) |
| CloudWatch Event Rule      | Event rule configuration (schedule, targets)                            |
| EC2 Console (Before/After) | Proof of AMI creation under “AMIs” tab                                  |
| EBS Console (Before/After) | Proof of new snapshots under “Snapshots” tab                            |
| CloudWatch Logs            | Logs showing backup activity, instance states, and snapshot status      |

---

### 🔐 **IAM Permissions for Lambda Role**

```json
{
  "Effect": "Allow",
  "Action": [
    "ec2:DescribeInstances",
    "ec2:DescribeVolumes",
    "ec2:DescribeSnapshots",
    "ec2:CreateImage",
    "ec2:CreateSnapshot",
    "ec2:CreateTags"
  ],
  "Resource": "*"
}
```

---

### ⚠️ **Problems Faced During Development**

| ❌ Problem                                         | 🧩 Cause                                                                      | ✅ Solution                                                                                                |
| ------------------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `return outside function`                         | Code block (EBS backup) was written outside `lambda_handler()`                | Moved all logic inside the function scope                                                                 |
| `UnauthorizedOperation (CreateTags)`              | Lambda's IAM role lacked permission                                           | Added `ec2:CreateTags` to the IAM policy                                                                  |
| `InvalidAMIName.Duplicate`                        | Duplicate AMI name for the same instance                                      | Appended date-time stamp to ensure uniqueness                                                             |
| `SnapshotCreationPerVolumeRateExceeded`           | Created snapshots too quickly                                                 | Introduced a 2-second sleep between snapshot requests                                                     |
| `Task timed out after 3.00 seconds`               | Lambda timeout was too short for all API operations                           | Increased timeout in Lambda settings to 5+ minutes                                                        |
| `Instance state is stopped` or `not in 'running'` | Lambda tried to create AMI while instance was in `stopped` or `pending` state | Added retry loop to wait up to 3 minutes for `running` state before proceeding; if not, skip AMI creation |
| No recent snapshot check failed                   | Missed `timezone` import for comparing snapshot times                         | Added `from datetime import timezone` to handle UTC timestamp logic correctly                             |

---

### ✅ **Key Takeaways**

* Scheduled automation using CloudWatch + Lambda is efficient and serverless.
* Backup reliability improves by waiting for the correct EC2 state.
* IAM permissions must be precisely granted.
* Error handling and retry logic are essential for real-world reliability.

---

