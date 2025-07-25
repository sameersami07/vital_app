require('dotenv').config();
const mongoose = require("mongoose");

const { exec } = require('child_process');
const cors = require('cors');
const bodyParser = require('body-parser');

const app = require("./app");

// IMPORTED ROUTES
const authRoutes = require("./routes/auth");
const userRoutes = require("./routes/user");
const questionRoutes = require("./routes/question");

// ROUTES
app.use(cors());
app.use(bodyParser.json());
app.use("/api/auth", authRoutes);
app.use("/api/users", userRoutes);
app.use("/api/questions", questionRoutes);

// POST endpoint for recommendations
app.post('/run-python', (req, res) => {
  const { age, description, brand, market_status, allergies } = req.body;

  if (!age || !description) {
    return res.status(400).json({ error: 'age and description are required' });
  }

  // Default values if not provided
  const safeBrand = brand || "Vega";
  const safeMarketStatus = market_status !== undefined ? market_status : "False";
  const safeAllergies = allergies || "";

  const command = `python check.py --age ${age} --brand "${safeBrand}" --market_status ${safeMarketStatus} --description "${description}" --allergies "${safeAllergies}"`;

  exec(command, { timeout: 20000, maxBuffer: 1024 * 1024 }, (error, stdout, stderr) => {
    console.log("STDOUT:", stdout);
    console.error("STDERR:", stderr);

    if (error) {
      console.error(`Error executing Python script: ${error}`);
      return res.status(501).json({ error: 'Description is not specific enough, hence, no detection.' });
    }

    try {
      const result = JSON.parse(stdout);
      res.json(result);
    } catch (parseError) {
      console.error(`Error parsing Python script output: ${parseError}`);
      res.status(500).json({ error: 'Internal Server Error', details: stdout });
    }
  });
});

// MONGOOSE SETUP
const PORT = process.env.PORT || 3001;
mongoose
  .connect(process.env.MONGO_URL, {})
  .then(() => {
    if (process.env.NODE_ENV !== "test") {
      app.listen(PORT, () => console.log(`Server Port: ${PORT}`));
    }
  })
  .catch((error) => console.log(`${error} did not connect`));

module.exports = app;