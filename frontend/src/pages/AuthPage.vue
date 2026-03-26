<template>
  <section class="auth-wrap">
    <article class="card auth-card">
      <div class="auth-tabs">
        <button class="btn" :class="{ 'btn-accent': mode === 'login' }" @click="switchMode('login')">Login</button>
        <button class="btn" :class="{ 'btn-accent': mode === 'register' }" @click="switchMode('register')">Register</button>
      </div>

      <div v-if="mode === 'login'" class="auth-form">
        <input class="input" v-model.trim="loginForm.username" placeholder="Username" autocomplete="username" />
        <input
          class="input"
          v-model="loginForm.password"
          type="password"
          placeholder="Password"
          autocomplete="current-password"
          @keyup.enter="login"
        />
        <button class="btn btn-accent" :disabled="auth.loading" @click="login">Login</button>
      </div>

      <div v-else class="auth-form">
        <input class="input" v-model.trim="registerForm.username" placeholder="Username" autocomplete="username" />
        <input class="input" v-model.trim="registerForm.email" placeholder="Email" autocomplete="email" />
        <input class="input" v-model.trim="registerForm.school_name" placeholder="School (optional)" />
        <input
          class="input"
          v-model="registerForm.password"
          type="password"
          placeholder="Password"
          autocomplete="new-password"
        />

        <div class="captcha-card">
          <div class="captcha-header">
            <span class="captcha-title">Registration Check</span>
            <button class="btn btn-ghost" type="button" :disabled="challengeLoading" @click="loadRegisterChallenge">
              {{ challengeLoading ? "Refreshing..." : "New Question" }}
            </button>
          </div>
          <p class="captcha-prompt">
            {{ registerChallenge.prompt || "Loading verification question..." }}
          </p>
          <input
            class="input"
            v-model.trim="registerForm.captcha_answer"
            placeholder="Enter the result"
            inputmode="numeric"
            @keyup.enter="register"
          />
          <p v-if="registerChallenge.expires_in_seconds" class="captcha-meta">
            This question is valid for {{ Math.ceil(registerChallenge.expires_in_seconds / 60) }} minutes.
          </p>
        </div>

        <div class="trap-field" aria-hidden="true">
          <label for="register-website">Website</label>
          <input
            id="register-website"
            v-model="registerForm.website"
            type="text"
            autocomplete="off"
            tabindex="-1"
          />
        </div>

        <button class="btn btn-accent" :disabled="auth.loading || challengeLoading" @click="register">Register</button>
      </div>

      <p v-if="errorMsg" class="meta error-text">{{ errorMsg }}</p>
    </article>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import api from "../services/api";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const mode = ref("login");
const errorMsg = ref("");
const challengeLoading = ref(false);
const registerChallenge = reactive({
  prompt: "",
  token: "",
  expires_in_seconds: 0,
});

const loginForm = reactive({
  username: "",
  password: "",
});

const registerForm = reactive({
  username: "",
  email: "",
  school_name: "",
  password: "",
  captcha_answer: "",
  website: "",
});

function getErrorText(error, fallback) {
  const payload = error?.response?.data;
  if (!payload) return fallback;
  if (typeof payload === "string") return payload;
  if (typeof payload.detail === "string") return payload.detail;
  if (Array.isArray(payload)) return payload.join("; ");
  if (typeof payload === "object") {
    const items = [];
    for (const [key, value] of Object.entries(payload)) {
      if (key === "request_id") continue;
      if (Array.isArray(value)) {
        items.push(`${key}: ${value.join("; ")}`);
      } else if (typeof value === "string") {
        items.push(`${key}: ${value}`);
      }
    }
    if (items.length) return items.join("; ");
  }
  return fallback;
}

function switchMode(nextMode) {
  mode.value = nextMode;
  errorMsg.value = "";
  if (nextMode === "register" && !registerChallenge.token && !challengeLoading.value) {
    loadRegisterChallenge();
  }
}

async function loadRegisterChallenge() {
  challengeLoading.value = true;
  try {
    const { data } = await api.get("/auth/register-challenge/");
    registerChallenge.prompt = data.prompt || "";
    registerChallenge.token = data.token || "";
    registerChallenge.expires_in_seconds = Number(data.expires_in_seconds || 0);
    registerForm.captcha_answer = "";
    registerForm.website = "";
  } catch (error) {
    errorMsg.value = getErrorText(error, "Failed to load the verification question.");
  } finally {
    challengeLoading.value = false;
  }
}

async function login() {
  errorMsg.value = "";
  try {
    await auth.login(loginForm);
    await router.push({ name: "profile" });
  } catch (error) {
    errorMsg.value = getErrorText(error, "Login failed");
  }
}

async function register() {
  errorMsg.value = "";

  if (!registerChallenge.token) {
    await loadRegisterChallenge();
    if (!registerChallenge.token) return;
  }

  try {
    await auth.register({
      username: registerForm.username,
      email: registerForm.email,
      school_name: registerForm.school_name,
      password: registerForm.password,
      captcha_token: registerChallenge.token,
      captcha_answer: registerForm.captcha_answer,
      website: registerForm.website,
    });
    await router.push({ name: "profile" });
  } catch (error) {
    errorMsg.value = getErrorText(error, "Registration failed");
    await loadRegisterChallenge();
  }
}

onMounted(() => {
  if (mode.value === "register") {
    loadRegisterChallenge();
  }
});
</script>

<style scoped>
.auth-wrap {
  display: grid;
  place-items: center;
  min-height: calc(100vh - 180px);
}

.auth-card {
  width: min(520px, 100%);
  padding: 20px;
}

.auth-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.auth-form {
  display: grid;
  gap: 10px;
}

.captcha-card {
  display: grid;
  gap: 10px;
  padding: 14px;
  border: 1px solid var(--line-color, #d7deea);
  border-radius: 16px;
  background: rgba(244, 247, 252, 0.8);
}

.captcha-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.captcha-title {
  font-size: 13px;
  font-weight: 700;
}

.captcha-prompt {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.captcha-meta {
  margin: 0;
  font-size: 12px;
  color: var(--text-muted, #6b7280);
}

.btn-ghost {
  border-style: dashed;
}

.trap-field {
  position: absolute;
  left: -9999px;
  width: 1px;
  height: 1px;
  overflow: hidden;
}

.error-text {
  margin-top: 12px;
  color: #c03636;
}
</style>
