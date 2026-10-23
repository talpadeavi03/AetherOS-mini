#ifndef MCP_H
#define MCP_H

#include "types.h"

#define MCP_MAX_TOOLS 32
#define MCP_MAX_RESOURCES 32
#define MCP_EVENT_LOG_SIZE 64

typedef void (*mcp_tool_fn)(const char *args, char *output, size_t out_max);
typedef void (*mcp_resource_read_fn)(char *output, size_t out_max);

struct mcp_tool {
    char name[48];
    char description[128];
    char schema[64];
    mcp_tool_fn execute;
};

struct mcp_resource {
    char uri[48];
    char description[128];
    mcp_resource_read_fn read;
};

struct mcp_event {
    u64 timestamp_ms;
    char source[24];
    char message[96];
};

void mcp_init(void);

// Tool registration & invocation
bool mcp_register_tool(const char *name, const char *description, const char *schema, mcp_tool_fn fn);
bool mcp_call_tool(const char *name, const char *args, char *output, size_t out_max);
size_t mcp_get_tools_count(void);
const struct mcp_tool *mcp_get_tool(size_t index);

// Resource registration & reading
bool mcp_register_resource(const char *uri, const char *description, mcp_resource_read_fn read_fn);
bool mcp_read_resource(const char *uri, char *output, size_t out_max);
size_t mcp_get_resources_count(void);
const struct mcp_resource *mcp_get_resource(size_t index);

// Event publishing & streaming
void mcp_publish_event(const char *source, const char *message);
size_t mcp_get_events_count(void);
const struct mcp_event *mcp_get_event(size_t index);

#endif // MCP_H
