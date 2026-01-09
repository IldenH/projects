const fs = require("fs");
const path = require("path");

let users = [];

const filePath = path.join(__dirname, "users.csv");
fs.readFile(filePath, "utf8", (err, data) => {
  if (err) {
    return console.error("Erorr reading file " + filePath + ": " + err);
  }
  let lines = data.split("\n");
  lines.pop();
  let headers = lines[0].split(";");
  for (let line of lines) {
    let vals = line.split(";");
    let user = {};
    for (let i in vals) {
      user[headers[i]] = vals[i];
    }
    users.push(user);
  }
  for (let i = 0; i < 5; i++) {
    let randIndex = Math.floor(Math.random() * users.length);
    let user = users[randIndex];
    console.log(
      user["First name"] + " " + user["Last name"] + " (" + user.Username + ")",
    );
    users.splice(randIndex, 1);
  }
});
