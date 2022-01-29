require ["fileinto", "mailbox"];

if anyof(header :contains "X-Spam" "Yes",
         header :contains "X-Spam-Status" "Yes",
         header :matches "X-Spam-Flag" "YES") {
  fileinto :create "Junk";
  stop;
}
