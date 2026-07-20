import { getRequestConfig } from "next-intl/server";

import { messages } from "./messages";

export default getRequestConfig(async () => {
  return {
    locale: "pt-BR",
    messages,
  };
});
