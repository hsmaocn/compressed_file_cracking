#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <archive.h>
#include <archive_entry.h>
#include <iconv.h>
#include <errno.h>

#define MAX_PASSWORD_LEN 100
#define MAX_THREADS 50

// 全局变量
char *zip_file_path = NULL;
FILE *dict_file = NULL;
int thread_count = 1;
pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;

// 日志函数
void log_error(const char *message) {
    FILE *log_file = fopen("error_log.txt", "a");
    if (log_file) {
        fprintf(log_file, "[%s] %s\n", __TIME__, message);
        fclose(log_file);
    }
}

// 验证压缩包完整性
int verify_archive(const char *path) {
    struct archive *a = archive_read_new();
    archive_read_support_format_all(a);
    archive_read_support_filter_all(a);

    if (archive_read_open_filename(a, path, 10240) != ARCHIVE_OK) {
        log_error("Archive is corrupted or cannot be opened.");
        archive_read_free(a);
        return 0;
    }

    archive_read_free(a);
    return 1;
}

// 尝试解压压缩包
int try_extract(const char *password) {
    struct archive *a = archive_read_new();
    archive_read_support_format_all(a);
    archive_read_support_filter_all(a);

    if (archive_read_set_passphrase(a, password) != ARCHIVE_OK) {
        log_error("Failed to set passphrase.");
        archive_read_free(a);
        return 0;
    }

    if (archive_read_open_filename(a, zip_file_path, 10240) != ARCHIVE_OK) {
        log_error("Failed to open archive with the given password.");
        archive_read_free(a);
        return 0;
    }

    // 解压成功
    archive_read_free(a);
    return 1;
}

// 线程函数
void *crack_password(void *arg) {
    char password[MAX_PASSWORD_LEN];
    while (1) {
        pthread_mutex_lock(&mutex);
        if (fgets(password, MAX_PASSWORD_LEN, dict_file) == NULL) {
            pthread_mutex_unlock(&mutex);
            break;
        }
        pthread_mutex_unlock(&mutex);

        // 去掉换行符
        password[strcspn(password, "\n")] = '\0';

        printf("Trying password: %s\n", password);

        if (try_extract(password)) {
            printf("Password found: %s\n", password);
            exit(0); // 找到密码后退出程序
        }
    }
    return NULL;
}

// 主函数
int main(int argc, char *argv[]) {
    if (argc < 4) {
        printf("Usage: %s <zip_file> <dict_file> <thread_count>\n", argv[0]);
        return 1;
    }

    zip_file_path = argv[1];
    dict_file = fopen(argv[2], "r");
    thread_count = atoi(argv[3]);

    if (!dict_file) {
        perror("Failed to open dictionary file");
        return 1;
    }

    if (!verify_archive(zip_file_path)) {
        printf("The archive is corrupted or invalid.\n");
        fclose(dict_file);
        return 1;
    }

    // 创建线程
    pthread_t threads[MAX_THREADS];
    for (int i = 0; i < thread_count; i++) {
        if (pthread_create(&threads[i], NULL, crack_password, NULL) != 0) {
            perror("Failed to create thread");
            return 1;
        }
    }

    // 等待线程完成
    for (int i = 0; i < thread_count; i++) {
        pthread_join(threads[i], NULL);
    }

    fclose(dict_file);
    printf("Password not found in the dictionary.\n");
    return 0;
}
