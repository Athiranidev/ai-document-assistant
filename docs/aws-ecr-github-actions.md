AWS ECR and GitHub Actions CI/CD Integration

This document records the AWS container registry and GitHub Actions
integration work completed after the existing EC2 and Docker deployment
documentation.

1. Objective
Prepare the AI Document Assistant project for an automated CI/CD
workflow in which GitHub Actions builds the Docker image and publishes
it to a private Amazon Elastic Container Registry (ECR) repository.

The intended authentication method is GitHub OpenID Connect (OIDC), so
the workflow can obtain short-lived AWS credentials by assuming an IAM
role rather than storing long-term AWS access keys in GitHub Secrets.

2. AWS project details
  Setting                                            Value
  AWS project                                        Assembly Required
AWS account ID                                     513051133769
AWS Region                                         ap-southeast-2
AWS CLI profile                                    ai-doc-assistant
ECR repository                                     ai-document-assistant
GitHub repository                                  Athiranidev/ai-document-assistant
GitHub branch permitted by the role trust policy   main

ECR repository URI
513051133769.dkr.ecr.ap-southeast-2.amazonaws.com/ai-document-assistant

3. AWS CLI authentication
AWS CLI authentication was established using the ai-doc-assistant
profile.

Command used:
aws login --profile ai-doc-assistant --region ap-southeast-2
The authenticated identity was checked with:
aws sts get-caller-identity --profile ai-doc-assistant
The returned account ID was 513051133769. For subsequent commands in
this phase, use the --profile ai-doc-assistant option and the
ap-southeast-2 region where the command requires a region.

The interactive aws login session is for local administration. GitHub
Actions will use OIDC instead of relying on this interactive login.

4. ECR repository and Docker image
A private ECR repository named ai-document-assistant exists in
ap-southeast-2.

A Docker image was pushed manually to this repository with the tag v1.

Image reference
513051133769.dkr.ecr.ap-southeast-2.amazonaws.com/ai-document-assistant:v1
The push completed successfully. The image was subsequently checked
using the AWS CLI.

Recorded image details:
- Tag: v1
- Image size: approximately 722 MB
- Image digest:
  sha256:06fc6bfecfa1581cf711cc5bf4dc4e3cdfe0c99f151474758620154c7130489e
This confirms that the repository can store the project's container
image. Automated publishing from GitHub Actions has not yet been
configured.

5. AWS Console and AWS CLI: feature availability observation
While attempting to create a GitHub OIDC identity provider through the
AWS Management Console, the Console displayed a message indicating that
the feature was unavailable in the current project experience and
suggested upgrading.

The equivalent operation was then attempted using the AWS CLI. AWS
accepted the API request and created the identity provider successfully.

This is the observed result for this specific operation:
- The Console workflow displayed an upgrade restriction.
- The IAM API request made through the CLI succeeded.
- The created provider was independently verified through the IAM API.
The exact reason for the difference has not been established. It may
relate to a Console workflow or project-experience limitation. This
result does not establish that every Console restriction can be
bypassed using the CLI. Each operation must be tested and its actual API
response checked.

6. GitHub OIDC identity provider
The GitHub Actions OIDC provider was created in IAM.

Command used:
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --tags Key=Purpose,Value=GitHubActionsECR \
  --profile ai-doc-assistant
Provider ARN
arn:aws:iam::513051133769:oidc-provider/token.actions.githubusercontent.com
The provider was verified with:
aws iam list-open-id-connect-providers \
  --profile ai-doc-assistant
The output included the provider ARN, confirming that it exists in the
AWS account.

7. GitHub Actions trust policy
A local trust-policy file was prepared at:
/tmp/github-ecr-trust-policy.json
Its policy document is:
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::513051133769:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:Athiranidev/ai-document-assistant:ref:refs/heads/main"
        }
      }
    }
  ]
}
The trust policy specifies:
- The GitHub Actions OIDC provider as the trusted federated identity.
- sts.amazonaws.com as the audience.
- The Athiranidev/ai-document-assistant repository's main branch
  as the permitted subject.
This trust policy determines which GitHub identity may request the role.
It does not, by itself, grant permission to push images to ECR.

8. IAM role creation
An IAM role named GitHubActionsECRRole was created successfully using
the trust-policy file.

Command used:
aws iam create-role \
  --role-name GitHubActionsECRRole \
  --assume-role-policy-document file:///tmp/github-ecr-trust-policy.json \
  --description "Allows GitHub Actions to publish images to ECR" \
  --profile ai-doc-assistant
Role ARN
arn:aws:iam::513051133769:role/GitHubActionsECRRole
The AWS CLI returned the role details and its trust relationship. The
role was also visible in the IAM Roles page in the AWS Management
Console.

At this point, the role has been created with its trust relationship.
The ECR publishing permissions have not yet been attached.

9. Current progress

  Task                                           Status

  AWS CLI authentication                         Completed
Private ECR repository available               Completed
Manual Docker image push (v1)                Completed
GitHub OIDC provider creation                  Completed
OIDC provider verification                     Completed
GitHub trust-policy preparation                Completed
GitHubActionsECRRole creation                Completed
ECR push-only permissions policy               Pending
Attach ECR policy to the role                  Pending
Verify role permissions                        Pending
Configure GitHub Actions OIDC authentication   Pending
Automate Docker image publishing to ECR        Pending
Test CI/CD workflow                            Pending
EC2 deployment using the automated image       Not started

10. Next steps

Step 1 -- Prepare an ECR push-only policy

Create a local policy file named:
/tmp/ecr-push-policy.json

The intended permissions are:
- ecr:GetAuthorizationToken on *, as required for ECR
  authentication.
- ecr:BatchCheckLayerAvailability
- ecr:InitiateLayerUpload
- ecr:UploadLayerPart
- ecr:CompleteLayerUpload
- ecr:PutImage
The image upload actions should be scoped to this repository:
arn:aws:ecr:ap-southeast-2:513051133769:repository/ai-document-assistant
The policy file has been proposed but its creation and attachment have
not yet been confirmed.

Step 2 -- Attach and verify the policy

Attach the narrowly scoped policy to GitHubActionsECRRole, then
inspect the role's attached and inline policies to verify the
permissions.

Step 3 -- Configure GitHub Actions

Update the existing workflow in:
.github/workflows/ci.yml
The workflow should:
1. Check out the repository.
2. Build the Docker image for CI runs.
3. Request GitHub's OIDC token permission.
4. On pushes to main, assume GitHubActionsECRRole.
5. Authenticate to ECR.
6. Push the image to the ai-document-assistant repository.
Pull-request builds should not receive permission to publish images to
ECR. The workflow conditions and permissions must enforce that
separation.

Step 4 -- Test the pipeline

Test both paths:
- A pull request should build the image without publishing it.
- A push to main should authenticate through OIDC, build the image
  and publish it to ECR.
Verify the resulting image tag and digest in ECR.
Step 5 -- Plan deployment
After the CI/CD publishing workflow is working, plan the EC2 deployment
separately. Do not launch or leave compute resources running without
checking the expected AWS charges.

11. Security notes

- Prefer GitHub OIDC and short-lived role credentials over long-term
  AWS access keys stored in GitHub.
- Keep the role trust policy restricted to the intended repository and
  branch.
- Grant only the ECR actions required for image publishing.
- Do not modify the AWS-managed AccountFullAccessRole.
- Do not put AWS credentials, tokens, passwords, or other secrets in
  this documentation.
- Review AWS resource usage and billing while working in the AWS
  project.
Last completed milestone: GitHub OIDC provider created and verified;
GitHubActionsECRRole created with the GitHub main branch trust
relationship.
