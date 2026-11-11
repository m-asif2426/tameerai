import AuthSplitScreen from "@/components/auth/AuthSplitScreen";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Create Account — TameerAI Construction Intelligence",
  description: "Register for TameerAI to analyze PBC 2021 building codes, contracts, and construction costs with AI.",
};

export default function SignupPage() {
  return <AuthSplitScreen initialMode="register" />;
}
