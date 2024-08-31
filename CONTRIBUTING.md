# Contributing
Here are some contributing guidelines for authors and reviewers of code changes.
The goal is a readable log of code changes, to enhance transparency of their
purpose and simplify debugging. Consider these guidelines as best practices, not
as absolute rules - we're all learning by doing, and imperfect changes and
commits are much better than none at all. For an introduction how to edit and
test the code, have look into the HACKING.md file. Note that you need some basic
understanding of Git to contribute; there are many tutorials in the Internet
that we cannot repeat here.


Naming conventions:
* 'Code change', 'patch', and 'commit' are used interchangeably.
* 'Author' and 'contributor' are used interchangeably.
* Git 'log' and 'history' are used interchangeably.
* PR, MR - pull request and merge request, used interchangeably.
* 'Merging' often means 'applying a patch to git history' in a general sense,
  not literal execution of the command `git merge`.


# For authors of patches
* If you would like to contribute, but are unsure what to do, just ask. There
  are usually also issues tagged as 'Contributor Invite' or 'beginner', which
  might be a good starting point to work on and have a known solution. Also,
  other developers are ready to guide you on the implementation for such tasks.
  Feel free to pickup a task from the issue by announcing it on the issue or by
  creating a new issue for whatever task you are going to work on.
* To get your changes included, you must open a merge request (MR) and get them
  reviewed. Briefly, fork the repository to your account, create a branch, edit
  code, commit and push there. Then you can create a merge request on the main
  repository.
* Before committing your changes ensure that your code conforms to base code
  hygiene by running tests (see HACKING.md) and the automatic code formatting
  tools `yapf` and `isort`. Please check also with `flake8`.
* Please include one single feature per merge request, to keep the review simple
  and focused on one topic. (This might still mean hundreds of lines of code.)
  Use a branch other than `main`, so you can create multiple merge requests
  and still keep merging from `main`. Depending on the complexity of your
  merge request, it may take a while until it is reviewed and merged.
* Keep your commits organized logically and as small as possible. If commit B
  fixes a mistake in commit A, both of which are part of the same merge request,
  combine them into a single commit. If commit A introduces a single logical
  change but breaks existing functionality and then commit B rectifies it, then
  also combine the two commits. This is to ensure that the source code can be
  checked out at any revision and used (such as during git bisect). If there are
  two unrelated changes in the same commit, split them to into separate commits.
  See Git documentation on how to merge, split and reorder commits.
* Please create meaningful commit messages, by following common guidelines:
    * Multiple lines are allowed if it makes the message clearer.
    * Separate the first subject line from the text body with a blank line.
	* Add the component you changed as the first word in the subject line.
    * Wrap the text at 72 characters.
    * Use the body to explain what your changes do, and maybe why and how it is
      achieved (the main idea).
	* Look into the git log to get an idea.
	* If it exists, mention the issue number.
	* End the message with a "Signed-off-by", see next entry.
* Consider adding `Signed-off-by: YOUR NAME <YOUR EMAIL>` into your commit
  message. With this, you explicitly certify that you have the rights to submit
  your work under the project's license (see LICENSES file) and that you agree
  to a [Developer Certificate of Origin](http://developercertificate.org/).
* If (part of) your code changes were inspired or plainly copied from another
  source, please indicate this in the merge request, so the reviewer can handle
  it.
* If your merge request is not ready for merging yet, the title of your merge
  request must start with
  `WIP:`
* If a reviewer asks for changes to your merge request, perform the changes as
  requested or provide clarification. Close the discussion threads so that the
  reviewer knows that it is ready for another round of review.
* Newer changes addressing review comments should go into the old commits which
  are being changed. For example, if there is a security problem with one of
  your commits, the commit should be edited instead of introducing a new commit
  with fix for it. After a merge, if a developer checks out any revision, it
  could not contain serious problem. See Git documentation on how to merge,
  split, reorder commits and how to force push your branches after altering
  commits.
* Have fun contributing :)


# For reviewers of patches

## How to review the work of others
* Be nice to contributors and give them opportunities to learn. Explain the
  reasons if you ask for changes instead of silently changing things yourself
  (unless trivial). This also saves you time in the future.
* Reviewers are expected to ensure that a contributor's work:
    * Does not break the current code. The code base should always be in a
	  usable state, without throwing (non-handled) errors. We also strive to
	  keep the code base in a release-worthy state.
    * Has no security issues.
    * Follows coding standards of the project
	  (mainly [PEP-8](https://www.python.org/dev/peps/pep-0008/)).
    * Is properly internationalized.
* Your main job is to make sure that the work runs as expected, by thoroughly
  testing the patch. New authors are usually not familiar with all areas of
  impact and may not have tested all cases. It is okay to rely on tests done by
  trusted authors, if they specify the specific cases they tested.
* When merging work from others, add this line to the commit message:
  `Reviewed-by: YOUR NAME <YOUR EMAIL>`.
* Some patches require knowledge of multiple technologies. If you are not
  familiar with all of them, it's fine to review only the portions you
  understand (and indicate them clearly). Then ask others for further review.
* For major architectural changes/decisions, consult others in the project
  before merging.
* You may make some minimal or obvious changes to the work before merging. If
  so, tell the contributor (and others) about your edits.
* In case more fundamental changes are necessary, or if the contributor is new,
  try to encourage them to make changes by giving appropriate feedback. This is
  a major way how we mentor new contributors.
* Any merge request whose title starts with `WIP:` cannot be merged. Communicate
  with the author on what the pending changes are. Get the author to complete
  them or complete them yourself in case of an emergency.
* Have fun reviewing :)


## Use of Git
* Avoid plain `git merge`, and use rebasing instead, to avoid merge commits.
  This keeps the history much more readable for others to understand, review,
  bisect and rollback.
* When merging patches with multiple commits, try to make each patch meaningful.
  For example, fixes to patches should be squashed into the original patch.
  Security issues and other serious issues should be avoided in intermediate
  patches – even if they are fixed in later patches.


## Use of GPG
* Sign all commits with GPG. This means avoiding GitLab's fancy merge and rebase
  buttons and doing it locally, where your private key is.
* In case a contributor signed with GPG, rebasing will strip it away. To
  compensate, put your GPG signature on the rebased commits. Given that we have
  to actually verify the signatures on each commit and the contributor may not
  be in our web of trust (as we allow anonymous contributions). In such cases,
  GPG signatures of the reviewers are more important.
* Get your GPG key signed by other reviewers or Debian Developers, to enable
  verification of your signed commits.


## (When) can I commit without review?
* Even if you have commit access, you should get your patches reviewed by the
  other reviewers.
* Certain patches do not require review. These include updating the manual, typo
  fixes, and creating new locales.
