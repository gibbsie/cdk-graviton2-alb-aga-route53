from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    core
)

with open('./ec2_ialb_aga_custom_r53/user_data/userdata.sh') as f:
    USER_DATA = f.read()


class EC2Stack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Latest Amazon Linux 2 AMI for ARM
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            cpu_type=ec2.AmazonLinuxCpuType.ARM_64)

        # Two roles, one for SSM and one with Secrets manager access.
        # This is so that the instance can read the secret value stored in SM
        role = iam.Role(self, "InstanceSSM",
                        assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(
            "service-role/AmazonEC2RoleforSSM"))
        role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite"))

        # Instance Type is a t4g.large with 128GB of EBS Storage, substitute more power/storage as appropriate.
        self.instance = ec2.Instance(
            self,
            "CodeServerInstance",
            instance_type=ec2.InstanceType("m6g.xlarge"),
            machine_image=amzn_linux,
            block_devices=[ec2.BlockDevice(
                device_name="/dev/xvda",
                volume=ec2.BlockDeviceVolume.ebs(
                    volume_size=128)
            )],
            vpc=vpc,
            role=role,
            user_data=ec2.UserData.custom(USER_DATA)
        )

        core.CfnOutput(self, "Output",
                       value=self.instance.instance_id)
