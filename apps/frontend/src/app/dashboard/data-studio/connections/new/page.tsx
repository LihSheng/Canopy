import { redirect } from "next/navigation";

export default function NewConnectionPage() {
  redirect("/dashboard/connections/sources");
}
