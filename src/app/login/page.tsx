import AuthSplitScreen from "@/components/auth/AuthSplitScreen";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Login — TameerAI Construction Intelligence",
  description: "Sign in to your TameerAI workspace for automated building code compliance and cost intelligence.",
};

export default function LoginPage() {
  return <AuthSplitScreen initialMode="login" />;
}
