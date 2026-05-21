import { redirect } from "next/navigation";
import { ROUTES } from "@/lib/constants";

export default function IngestionPage() {
  redirect(ROUTES.connections.home);
}
