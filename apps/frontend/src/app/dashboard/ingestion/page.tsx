import { redirect } from "next/navigation";
import { ROUTES } from "@/lib/constants";

const IngestionPage = () => {
  redirect(ROUTES.connections.home);
}
export default IngestionPage;
