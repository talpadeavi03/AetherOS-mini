#include "slm.h"
#include "mcp.h"
#include "string.h"
#include "serial.h"

static struct slm_chat_message chat_history[SLM_MAX_HISTORY];
static size_t history_count = 0;

static bool contains_word(const char *str, const char *word) {
    size_t str_len = strlen(str);
    size_t word_len = strlen(word);
    if (word_len > str_len) return false;

    for (size_t i = 0; i <= str_len - word_len; i++) {
        bool match = true;
        for (size_t j = 0; j < word_len; j++) {
            char c1 = str[i + j];
            char c2 = word[j];
            // case-insensitive match
            if (c1 >= 'A' && c1 <= 'Z') c1 += 32;
            if (c2 >= 'A' && c2 <= 'Z') c2 += 32;
            if (c1 != c2) {
                match = false;
                break;
            }
        }
        if (match) return true;
    }
    return false;
}

void slm_init(void) {
    history_count = 0;
    slm_add_to_history(false, "Hello! I am your Aether AI Copilot. Connected to kernel NeuroBus via MCP.");
    slm_add_to_history(false, "Type 'help', 'diagnose', 'threads', 'compact', or 'stats' to begin.");
    kprintf("[AetherOS] Embedded SLM Copilot Engine initialized.\n");
}

void slm_add_to_history(bool is_user, const char *msg) {
    if (history_count < SLM_MAX_HISTORY) {
        chat_history[history_count].is_user = is_user;
        strncpy(chat_history[history_count].text, msg, SLM_MSG_LEN - 1);
        chat_history[history_count].text[SLM_MSG_LEN - 1] = '\0';
        history_count++;
    } else {
        // Shift history up by 1
        for (size_t i = 0; i < SLM_MAX_HISTORY - 1; i++) {
            chat_history[i] = chat_history[i + 1];
        }
        chat_history[SLM_MAX_HISTORY - 1].is_user = is_user;
        strncpy(chat_history[SLM_MAX_HISTORY - 1].text, msg, SLM_MSG_LEN - 1);
        chat_history[SLM_MAX_HISTORY - 1].text[SLM_MSG_LEN - 1] = '\0';
    }
}

size_t slm_get_history_count(void) {
    return history_count;
}

const struct slm_chat_message *slm_get_history_message(size_t index) {
    if (index >= history_count) return NULL;
    return &chat_history[index];
}

void slm_query(const char *user_input, char *response_out, size_t max_len) {
    slm_add_to_history(true, user_input);

    if (contains_word(user_input, "diag") || contains_word(user_input, "health") || contains_word(user_input, "check")) {
        char diag_res[512];
        mcp_call_tool("ai.system_diagnose", "{}", diag_res, sizeof(diag_res));
        snprintf(response_out, max_len, "%s", diag_res);
    } else if (contains_word(user_input, "compact") || contains_word(user_input, "clean") || contains_word(user_input, "free")) {
        char comp_res[256];
        mcp_call_tool("kernel.mem_compact", "{}", comp_res, sizeof(comp_res));
        snprintf(response_out, max_len, "%s", comp_res);
    } else if (contains_word(user_input, "thread") || contains_word(user_input, "task") || contains_word(user_input, "process")) {
        char thread_res[384];
        mcp_read_resource("res://kernel/threads", thread_res, sizeof(thread_res));
        snprintf(response_out, max_len, "Active Threads on NeuroBus:\n%s", thread_res);
    } else if (contains_word(user_input, "stat") || contains_word(user_input, "info") || contains_word(user_input, "uptime")) {
        char stat_res[384];
        mcp_read_resource("res://kernel/stats", stat_res, sizeof(stat_res));
        snprintf(response_out, max_len, "Kernel Telemetry:\n%s", stat_res);
    } else if (contains_word(user_input, "tune") || contains_word(user_input, "boost") || contains_word(user_input, "fast")) {
        char tune_res[256];
        mcp_call_tool("kernel.thread_tune", "compositor_boost", tune_res, sizeof(tune_res));
        snprintf(response_out, max_len, "%s", tune_res);
    } else if (contains_word(user_input, "help")) {
        snprintf(response_out, max_len,
            "Aether AI Copilot Commands:\n"
            "- 'diagnose' : Comprehensive kernel health audit via MCP\n"
            "- 'threads'  : Inspect active threads & priorities\n"
            "- 'compact'  : Run memory coalescing & garbage cleanup\n"
            "- 'stats'    : Real-time telemetry (RAM, heap, uptime)\n"
            "- 'boost'    : Optimize UI compositor rendering pipeline");
    } else {
        snprintf(response_out, max_len,
            "Acknowledged: '%s'. Analyzed by NeuroBus SLM agent. Status is normal. Type 'help' for guidance.",
            user_input);
    }

    slm_add_to_history(false, response_out);
}
