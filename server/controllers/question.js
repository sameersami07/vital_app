const Question = require("../models/Question");

// Get all questions
const getAllQuestions = async (req, res) => {
  try {
    const questions = await  Question.find().find({user_id: "64b666666666666666666666"});   
    res.status(200).json(questions);
  } catch (err) {
    res.status(404).json({ message: err.message });
  }
};

// Get a question with questionId
const getMyQuestion = async (req, res) => {
  try {
    const { questionId } = req.params;
    const question = await Question.findById(questionId);
    res.status(200).json(question);
  } catch (err) {
    res.status(404).json({ message: err.message });
  }
};

// Get all questions with specific userId
const getMyQuestions = async (req, res) => {
  try {
    const { userId } = req.params;
    const questions = await Question.find({ user_id: userId });
    res.status(200).json(questions);
  } catch (err) {
    res.status(404).json({ message: err.message });
  }
};

// Create a Question
const createQuestion = async (req, res) => {
  try {
    const { gender, age, allergies, description, user_id } = req.body;

    const newQuestion = new Question({
      gender,
      age,
      allergies,
      description,
      user_id
    });

    const savedQuestion = await newQuestion.save();
    console.log("Question created successfully");
    return res.status(201).json(savedQuestion);
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
};

// UPDDATE A QUESTION
const updateQuestion = async (req, res) => {
  try {
    const { questionId } = req.params;
    const { rec_list } = req.body;

    const updatedQuestion = await Question.findByIdAndUpdate(
      questionId,
      {
        rec_list: rec_list,
      }
    );
    res.status(200).json(updatedQuestion);
  } catch (err) {
    res.status(404).json({ message: err.message });
  }
};

// Delete a question
const deleteQuestion = async (req, res) => {
  try {
    const { questionId } = req.params;
    await Question.findByIdAndDelete(questionId);
    return res.status(200).json({ success: true });
  } catch (err) {
    res.status(404).json({ success: false, message: err.message });
  }
};

module.exports = {
  getAllQuestions: getAllQuestions,
  getMyQuestion: getMyQuestion,
  getMyQuestions: getMyQuestions,
  createQuestion: createQuestion,
  updateQuestion: updateQuestion,
  deleteQuestion: deleteQuestion,
};