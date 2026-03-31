# CS222 Repository Initialization Exercise (PR #0)
# Before You Start (Read This First)
# Important: Make Sure You Are Working in the Correct Repository

This exercise must be completed in your **team repository**, not your individual repository.

You now have access to three types of repositories:

**1. Your Individual Repository**
- Created earlier in the semester using GitHub Classroom
- Used for earlier exercises
- Only you have access

**2. Your Team Repository**
- Shared with your teammates
- This is where your project work happens
- This is where you must complete this assignment

**3. The CS222 Course Resources Repository**
- Contains instructions and templates
- You should read files here but **do not submit work here**

Before starting the assignment, confirm that:

• you can see your teammates listed under the repository  
• the repository name includes your **team number**

If you do not see teammates listed in the repository, you are likely in the wrong repository.
This exercise verifies that you can access your **team repository** and use the **GitHub workflow required for CS222**.

You will:

- access your team repository
- create a branch
- add a document to the repository
- open a Pull Request (PR)
- review another student's Pull Request

This exercise also ensures that all students have **working GitHub access** before project work begins.

---

Most students who cannot access their repository have **not accepted one of the GitHub invitations**.

For this course you must accept **two different invitations**:

1. **Organization invitation**  
   Allows you to join the CS222 GitHub organization.

2. **Repository invitation**  
   Allows you to access your **team repository**.

These invitations are **different from the assignment you originally accepted** that created your **individual repository earlier in the course**.

You must accept **both invitations** before you will see your team repository.

---

# Where to Find GitHub Invitations

GitHub invitations do **not always arrive by email**.

The most reliable method is:

1. Log into GitHub
2. Click the **bell icon (Notifications)** in the upper-right corner
3. Look for invitations to:
   - join the **CS222 organization**
   - access your **team repository**

You can also go directly to:


https://github.com/notifications


Accept **all pending invitations**.

---

# Step 1 — Locate Your Team Repository

After accepting invitations:

Go to the organization page:


https://github.com/
<organization-name>


You should be able to see your **team repository** listed there.

If you cannot see the repository, read the **Troubleshooting** section later in this document.

---

# Step 2 — Create Your Document

Create a file in your team repository.

The file must be named:


docs/<netid>.md


Example:


docs/woodley.md

You may create this file using either:

- the **GitHub web interface**
- a **local Git clone**

Paste the **template provided in the assignment** into this file.

Note: If the folder "/docs" does not already exist,  GitHub will create it for you.

---

# Step 3 — Create a Branch

Do **not commit directly to `main`**.

Create a branch such as:


init-netid


Branches allow developers to make changes safely without affecting the main project.

---

# Step 4 — Commit Your File

Add the file and commit it.

Example commit message:


Add repository initialization document for <netid>


---

# Step 5 — Open a Pull Request

Push your branch to GitHub and open a **Pull Request (PR)**.

The PR will request that your change be merged into the `main` branch.

Pull Requests are the **standard workflow for CS222** and allow teammates to review changes before they become part of the project.

---

# Step 6 — Review a Teammate's Pull Request

Each student must review **one teammate's PR**.

When reviewing:

- read the document
- leave **at least one comment**
- approve the PR if appropriate

Code review is an important part of collaborative development.

---

# Step 7 — Merge the Pull Request

After your PR is reviewed and approved, it can be merged into `main`.

---

# Expected Repository Structure

After all team members complete the assignment, the repository should contain:


docs/
github-workflow-guide.md
netid1.md
netid2.md
netid3.md
netid4.md


Your file should appear inside the **docs directory** using your NetID as the filename.

---

# Troubleshooting Guide

If you encounter problems, review the sections below.

---

# Problem: I Cannot See the CS222 Organization

You likely have **not accepted the organization invitation**.

Check GitHub notifications:


https://github.com/notifications


Accept the invitation to join the organization.

---

# Problem: I Can See the Organization but Not My Team Repository

You may not have accepted the **repository invitation**.

This invitation is separate from the organization invitation.

Check notifications again:


https://github.com/notifications


Accept the invitation to access your **team repository**.

---

# Problem: I Accepted the Invitation but Still Cannot Access the Repo

Check the following.

## Confirm you are logged into the correct GitHub account

Some students accidentally use multiple GitHub accounts.

Verify your username in the upper-right corner of GitHub and ensure it matches the account you registered for the course.

---

## Confirm you are a member of the organization

Visit:


https://github.com/orgs/
<organization-name>/people


Your username should appear there.

---

# Problem: I Accidentally Committed Directly to `main`

This assignment requires using a **branch and Pull Request**.

If you committed directly to `main`, redo the exercise:

1. create a new branch
2. modify or re-add your file
3. commit the change
4. open a Pull Request

---

# Problem: My File Is in the Wrong Location

Your file must be located here:


docs/<netid>.md


Example:


docs/jdoe5.md


Common mistakes include:


netid.md
docs/docs/netid.md
docs/john.md


Move the file to the correct location and update your PR.

---

# Problem: I Created the File but Did Not Open a Pull Request

Creating a commit **does not complete the assignment**.

You must open a Pull Request.

Steps:

1. go to your repository
2. click the **Pull Requests** tab
3. click **New Pull Request**
4. select your branch
5. create the PR

---

# Problem: I Cannot Review Another Student's Pull Request

Make sure:

- you are a collaborator on the repository
- you are logged into the correct GitHub account

Then:

1. open the **Pull Requests** tab
2. select a teammate's PR
3. click **Review changes**
4. leave a comment

---

# Problem: My Branch Cannot Be Merged

Another PR may have been merged first.

Your branch may need to be updated with the latest version of `main`.

If you are unsure how to do this, ask your mentor.

---

# When to Contact Course Staff

If you still cannot complete the assignment, contact course staff and include:

- your **GitHub username**
- your **NetID**
- the **name of your team repository**
- a **screenshot of your GitHub notifications page**

Providing this information will allow us to resolve the issue quickly.
