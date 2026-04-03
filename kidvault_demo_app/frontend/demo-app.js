const API_BASE = "/api";

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.message || "Request failed");
  }
  return data;
}

function byId(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const element = byId(id);
  if (element) {
    element.textContent = value;
  }
}

function setStatus(id, value, className = "") {
  const element = byId(id);
  if (!element) {
    return;
  }
  element.textContent = value;
  element.className = `status ${className}`.trim();
}

function updateCommonState(state) {
  if (!state) {
    return;
  }

  const challenge = state.challenge;

  setText("home-summary", `${challenge.subject} challenge for ${challenge.grade} with reward Rs ${challenge.reward}. Wallet balance: Rs ${state.wallet_balance}.`);

  setText("parent-subject", challenge.subject);
  setText("parent-grade", challenge.grade);
  setText("parent-reward", `Rs ${challenge.reward}`);
  setText("parent-levels", `${challenge.levels} levels`);
  setStatus("parent-request-status", state.request_status, state.reward_request?.status === "approved" ? "success" : state.reward_request ? "pending" : "");
  setStatus("parent-approval-status", state.approval_status, state.reward_request?.status === "approved" ? "success" : state.reward_request ? "pending" : "");

  setText("kid-subject", challenge.subject);
  setText("kid-grade", challenge.grade);
  setText("kid-levels", `${challenge.levels} levels`);
  setText("kid-reward", `Rs ${challenge.reward}`);
  setText("kid-progress-count", `${challenge.completed_levels} / ${challenge.levels}`);
  setStatus("kid-status", challenge.completed_levels >= challenge.levels ? "Challenge complete" : "Challenge active", challenge.completed_levels >= challenge.levels ? "success" : "");

  setText("quiz-subject", challenge.subject);
  setText("quiz-grade", challenge.grade);
  setText("quiz-question-text", state.quiz.text);

  setText("reward-amount", `Rs ${challenge.reward}`);
  setStatus("reward-status", state.reward_status, state.reward_request?.status === "approved" ? "success" : state.reward_request ? "pending" : challenge.completed_levels >= challenge.levels ? "success" : "");
  setText("wallet-balance-copy", `Wallet balance: Rs ${state.wallet_balance}`);

  const subjectSelect = byId("challenge-subject");
  const gradeSelect = byId("challenge-grade");
  const rewardInput = byId("challenge-reward");
  const levelsInput = byId("challenge-levels");

  if (subjectSelect) {
    subjectSelect.value = challenge.subject;
  }
  if (gradeSelect) {
    gradeSelect.value = challenge.grade;
  }
  if (rewardInput) {
    rewardInput.value = challenge.reward;
  }
  if (levelsInput) {
    levelsInput.value = challenge.levels;
  }

  const optionButtons = document.querySelectorAll(".option");
  if (optionButtons.length === state.quiz.options.length) {
    optionButtons.forEach((button, index) => {
      button.textContent = state.quiz.options[index];
      button.dataset.value = state.quiz.options[index];
      button.classList.remove("correct", "wrong");
    });
  }
}

function setupParentActions(loadState) {
  const saveButton = byId("create-challenge");
  const resetButton = byId("parent-reset");
  const approveButton = byId("approve-reward");

  if (saveButton) {
    saveButton.addEventListener("click", async () => {
      try {
        await api("/challenge", {
          method: "POST",
          body: JSON.stringify({
            subject: byId("challenge-subject").value,
            grade: byId("challenge-grade").value,
            reward: byId("challenge-reward").value,
            levels: byId("challenge-levels").value,
          }),
        });
        await loadState();
        window.alert("Challenge saved.");
      } catch (error) {
        window.alert(error.message);
      }
    });
  }

  if (resetButton) {
    resetButton.addEventListener("click", async () => {
      try {
        await api("/reset", { method: "POST", body: JSON.stringify({}) });
        await loadState();
        window.alert("Demo reset.");
      } catch (error) {
        window.alert(error.message);
      }
    });
  }

  if (approveButton) {
    approveButton.addEventListener("click", async () => {
      try {
        await api("/reward/approve", { method: "POST", body: JSON.stringify({}) });
        await loadState();
        window.alert("Reward approved.");
      } catch (error) {
        window.alert(error.message);
      }
    });
  }
}

function setupQuizActions(loadState) {
  const submitButton = byId("submit-answer");
  const result = byId("quiz-result");
  let selected = "";

  document.querySelectorAll(".option").forEach((button) => {
    button.addEventListener("click", () => {
      selected = button.dataset.value;
      document.querySelectorAll(".option").forEach((item) => item.classList.remove("correct", "wrong"));
      button.classList.add("correct");
    });
  });

  if (submitButton) {
    submitButton.addEventListener("click", async () => {
      try {
        const data = await api("/quiz/answer", {
          method: "POST",
          body: JSON.stringify({ selected_answer: selected }),
        });
        document.querySelectorAll(".option").forEach((button) => {
          if (button.dataset.value === data.correct_answer) {
            button.classList.add("correct");
          } else if (button.dataset.value === selected && !data.correct) {
            button.classList.add("wrong");
          }
        });
        result.textContent = `${data.message} Correct answer: ${data.correct_answer}`;
        result.classList.remove("hidden");
        await loadState();
      } catch (error) {
        window.alert(error.message);
      }
    });
  }
}

function setupRewardActions(loadState) {
  const sendButton = byId("send-request");
  if (sendButton) {
    sendButton.addEventListener("click", async () => {
      try {
        await api("/reward/request", { method: "POST", body: JSON.stringify({}) });
        await loadState();
        window.alert("Reward request sent.");
      } catch (error) {
        window.alert(error.message);
      }
    });
  }
}

async function bootstrap() {
  const loadState = async () => {
    const data = await api("/state");
    updateCommonState(data.state);
  };

  await loadState();
  setupParentActions(loadState);
  setupQuizActions(loadState);
  setupRewardActions(loadState);
}

document.addEventListener("DOMContentLoaded", () => {
  if (!document.body.dataset.page) {
    return;
  }
  bootstrap().catch((error) => {
    console.error(error);
    window.alert("Could not connect to the KidVault demo backend. Start the Flask server first.");
  });
});
