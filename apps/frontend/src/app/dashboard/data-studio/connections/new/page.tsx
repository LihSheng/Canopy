import { redirect } from "next/navigation";

const NewConnectionPage = () => {
  redirect("/dashboard/connections/sources");
}
export default NewConnectionPage;
