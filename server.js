const express = require("express");
const mongoose = require("mongoose");
const bcrypt = require("bcryptjs");
const session = require("express-session");
const bodyParser = require("body-parser");

const app = express();

// Middleware
app.use(bodyParser.urlencoded({ extended: false }));
app.use(bodyParser.json());
app.use(express.static("public"));

app.use(session({
    secret: "carbonSecret",
    resave: false,
    saveUninitialized: false
}));

// MongoDB Connection
mongoose.connect("mongodb://127.0.0.1:27017/carbonDB")
.then(() => console.log("MongoDB Connected"))
.catch(err => console.log(err));

// User Schema
const User = require("./models/User");

// SIGNUP
app.post("/signup", async (req, res) => {
    const { name, email, password } = req.body;

    const hashedPassword = await bcrypt.hash(password, 10);

    const user = new User({
        name,
        email,
        password: hashedPassword,
        credits: 0
    });

    await user.save();
    res.redirect("/login.html");
});

// LOGIN
app.post("/login", async (req, res) => {
    const { email, password } = req.body;

    const user = await User.findOne({ email });

    if (!user) return res.send("User not found");

    const isMatch = await bcrypt.compare(password, user.password);

    if (!isMatch) return res.send("Wrong password");

    req.session.userId = user._id;
    res.redirect("/index.html");
});

// GET USER CREDITS
app.get("/credits", async (req, res) => {
    if (!req.session.userId) return res.json({ loggedIn: false });

    const user = await User.findById(req.session.userId);
    res.json({ loggedIn: true, credits: user.credits });
});

// ADD CREDIT
app.post("/add-credit", async (req, res) => {
    if (!req.session.userId) return res.json({ success: false });

    const { credit } = req.body;

    const user = await User.findById(req.session.userId);
    user.credits += credit;
    await user.save();

    res.json({ success: true, totalCredits: user.credits });
});

// LOGOUT
app.get("/logout", (req, res) => {
    req.session.destroy();
    res.redirect("/login.html");
});

app.listen(3000, () => console.log("Server running on port 3000"));
