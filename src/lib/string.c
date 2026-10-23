#include "string.h"

void *memcpy(void *dest, const void *src, size_t n) {
    u8 *d = (u8 *)dest;
    const u8 *s = (const u8 *)src;
    for (size_t i = 0; i < n; i++) {
        d[i] = s[i];
    }
    return dest;
}

void *memset(void *s, int c, size_t n) {
    u8 *p = (u8 *)s;
    for (size_t i = 0; i < n; i++) {
        p[i] = (u8)c;
    }
    return s;
}

void *memmove(void *dest, const void *src, size_t n) {
    u8 *d = (u8 *)dest;
    const u8 *s = (const u8 *)src;
    if (d < s) {
        for (size_t i = 0; i < n; i++) {
            d[i] = s[i];
        }
    } else if (d > s) {
        for (size_t i = n; i > 0; i--) {
            d[i - 1] = s[i - 1];
        }
    }
    return dest;
}

int memcmp(const void *s1, const void *s2, size_t n) {
    const u8 *p1 = (const u8 *)s1;
    const u8 *p2 = (const u8 *)s2;
    for (size_t i = 0; i < n; i++) {
        if (p1[i] != p2[i]) {
            return (int)p1[i] - (int)p2[i];
        }
    }
    return 0;
}

size_t strlen(const char *s) {
    size_t len = 0;
    while (s[len]) len++;
    return len;
}

int strcmp(const char *s1, const char *s2) {
    while (*s1 && (*s1 == *s2)) {
        s1++;
        s2++;
    }
    return *(const unsigned char *)s1 - *(const unsigned char *)s2;
}

int strncmp(const char *s1, const char *s2, size_t n) {
    for (size_t i = 0; i < n; i++) {
        if (s1[i] != s2[i]) {
            return (int)(unsigned char)s1[i] - (int)(unsigned char)s2[i];
        }
        if (s1[i] == '\0') {
            return 0;
        }
    }
    return 0;
}

char *strcpy(char *dest, const char *src) {
    char *orig = dest;
    while ((*dest++ = *src++));
    return orig;
}

char *strncpy(char *dest, const char *src, size_t n) {
    size_t i = 0;
    for (; i < n && src[i] != '\0'; i++) {
        dest[i] = src[i];
    }
    for (; i < n; i++) {
        dest[i] = '\0';
    }
    return dest;
}

char *strcat(char *dest, const char *src) {
    char *orig = dest;
    while (*dest) dest++;
    while ((*dest++ = *src++));
    return orig;
}

static void itoa_dec(s64 val, char *buf, size_t *pos, size_t max) {
    if (val == 0) {
        if (*pos + 1 < max) buf[(*pos)++] = '0';
        return;
    }
    if (val < 0) {
        if (*pos + 1 < max) buf[(*pos)++] = '-';
        val = -val;
    }
    char temp[32];
    int idx = 0;
    while (val > 0) {
        temp[idx++] = '0' + (val % 10);
        val /= 10;
    }
    for (int j = idx - 1; j >= 0; j--) {
        if (*pos + 1 < max) buf[(*pos)++] = temp[j];
    }
}

static void uitoa_dec(u64 val, char *buf, size_t *pos, size_t max) {
    if (val == 0) {
        if (*pos + 1 < max) buf[(*pos)++] = '0';
        return;
    }
    char temp[32];
    int idx = 0;
    while (val > 0) {
        temp[idx++] = '0' + (val % 10);
        val /= 10;
    }
    for (int j = idx - 1; j >= 0; j--) {
        if (*pos + 1 < max) buf[(*pos)++] = temp[j];
    }
}

static void itoa_hex(u64 val, char *buf, size_t *pos, size_t max, bool uppercase, int min_digits) {
    const char *digits = uppercase ? "0123456789ABCDEF" : "0123456789abcdef";
    char temp[32];
    int idx = 0;
    if (val == 0) {
        temp[idx++] = '0';
    } else {
        while (val > 0) {
            temp[idx++] = digits[val & 0xF];
            val >>= 4;
        }
    }
    while (idx < min_digits) {
        temp[idx++] = '0';
    }
    for (int j = idx - 1; j >= 0; j--) {
        if (*pos + 1 < max) buf[(*pos)++] = temp[j];
    }
}

int vsnprintf(char *str, size_t size, const char *format, va_list args) {
    if (size == 0) return 0;
    size_t pos = 0;

    for (size_t i = 0; format[i] != '\0'; i++) {
        if (format[i] != '%') {
            if (pos + 1 < size) str[pos++] = format[i];
            continue;
        }
        i++;
        if (format[i] == '\0') break;

        // Check for padding/digits like %02x, %08x, %016llx
        int pad_zeros = 0;
        if (format[i] == '0') {
            i++;
            while (format[i] >= '0' && format[i] <= '9') {
                pad_zeros = pad_zeros * 10 + (format[i] - '0');
                i++;
            }
        }

        // Length modifiers
        bool is_long = false;
        bool is_long_long = false;
        if (format[i] == 'l') {
            is_long = true;
            i++;
            if (format[i] == 'l') {
                is_long_long = true;
                i++;
            }
        }

        char spec = format[i];
        if (spec == '%') {
            if (pos + 1 < size) str[pos++] = '%';
        } else if (spec == 'c') {
            char c = (char)va_arg(args, int);
            if (pos + 1 < size) str[pos++] = c;
        } else if (spec == 's') {
            const char *s = va_arg(args, const char *);
            if (!s) s = "(null)";
            while (*s && pos + 1 < size) {
                str[pos++] = *s++;
            }
        } else if (spec == 'd' || spec == 'i') {
            s64 val;
            if (is_long_long || is_long) val = va_arg(args, s64);
            else val = va_arg(args, int);
            itoa_dec(val, str, &pos, size);
        } else if (spec == 'u') {
            u64 val;
            if (is_long_long || is_long) val = va_arg(args, u64);
            else val = va_arg(args, unsigned int);
            uitoa_dec(val, str, &pos, size);
        } else if (spec == 'x' || spec == 'X') {
            u64 val;
            if (is_long_long || is_long) val = va_arg(args, u64);
            else val = va_arg(args, unsigned int);
            itoa_hex(val, str, &pos, size, (spec == 'X'), pad_zeros);
        } else if (spec == 'p') {
            u64 val = (u64)va_arg(args, void *);
            if (pos + 2 < size) {
                str[pos++] = '0';
                str[pos++] = 'x';
            }
            itoa_hex(val, str, &pos, size, false, 16);
        }
    }

    if (pos < size) {
        str[pos] = '\0';
    } else {
        str[size - 1] = '\0';
    }
    return (int)pos;
}

int snprintf(char *str, size_t size, const char *format, ...) {
    va_list args;
    va_start(args, format);
    int ret = vsnprintf(str, size, format, args);
    va_end(args);
    return ret;
}
