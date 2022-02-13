require ["fileinto", "mailbox"];

if header :is "X-Spam" "Yes" {
  fileinto :create "Junk";
}
