#ifndef SLM_H
#define SLM_H

#include "types.h"

#define SLM_MAX_HISTORY 8
#define SLM_MSG_LEN 256

struct slm_chat_message {
    bool is_user;
    char text[SLM_MSG_LEN];
};

void slm_init(void);
void slm_query(const char *user_input, char *response_out, size_t max_len);
void slm_add_to_history(bool is_user, const char *msg);
size_t slm_get_history_count(void);
const struct slm_chat_message *slm_get_history_message(size_t index);

#endif // SLM_H
