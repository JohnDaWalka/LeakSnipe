#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define MAX_HANDS    1000
#define MAX_PLAYERS  10
#define SAVE_FILE    "poker_hands.dat"

typedef enum {
    RESULT_WIN,
    RESULT_LOSS,
    RESULT_FOLD,
    RESULT_SPLIT
} HandResult;

typedef struct {
    int id;
    char date[64];           // YYYY-MM-DD HH:MM
    char table_name[64];
    char hole_cards[8];      // e.g. "AhKs"
    char board[20];          // e.g. "Qh9d3cTh2s"
    char hand_type[32];      // e.g. "Flush", "Two Pair"
    int  num_players;
    double pot_size;
    double coin_in;          // coins wagered
    double coin_out;         // coins received
    HandResult result;
} PokerHand;

static PokerHand hands[MAX_HANDS];
static int hand_count = 0;

static const char *result_str(HandResult r) {
    switch (r) {
        case RESULT_WIN:   return "WIN";
        case RESULT_LOSS:  return "LOSS";
        case RESULT_FOLD:  return "FOLD";
        case RESULT_SPLIT: return "SPLIT";
        default:           return "???";
    }
}

static HandResult parse_result(const char *s) {
    if (strcasecmp(s, "win")   == 0) return RESULT_WIN;
    if (strcasecmp(s, "loss")  == 0) return RESULT_LOSS;
    if (strcasecmp(s, "fold")  == 0) return RESULT_FOLD;
    if (strcasecmp(s, "split") == 0) return RESULT_SPLIT;
    return RESULT_LOSS;
}

/* ---------- persistence ---------- */

static int save_hands(void) {
    FILE *fp = fopen(SAVE_FILE, "wb");
    if (!fp) { perror("save"); return -1; }
    fwrite(&hand_count, sizeof(hand_count), 1, fp);
    fwrite(hands, sizeof(PokerHand), hand_count, fp);
    fclose(fp);
    printf("  Saved %d hand(s) to %s\n", hand_count, SAVE_FILE);
    return 0;
}

static int load_hands(void) {
    FILE *fp = fopen(SAVE_FILE, "rb");
    if (!fp) return 0;   // first run, nothing to load
    fread(&hand_count, sizeof(hand_count), 1, fp);
    if (hand_count > MAX_HANDS) hand_count = MAX_HANDS;
    fread(hands, sizeof(PokerHand), hand_count, fp);
    fclose(fp);
    printf("  Loaded %d hand(s) from %s\n", hand_count, SAVE_FILE);
    return hand_count;
}

/* ---------- helpers ---------- */

static void clear_line(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF);
}

static void read_string(const char *prompt, char *buf, int maxlen) {
    printf("  %s: ", prompt);
    if (!fgets(buf, maxlen, stdin)) buf[0] = '\0';
    buf[strcspn(buf, "\n")] = '\0';
}

static double read_double(const char *prompt) {
    double v = 0;
    printf("  %s: ", prompt);
    if (scanf("%lf", &v) != 1) v = 0;
    clear_line();
    return v;
}

static int read_int(const char *prompt) {
    int v = 0;
    printf("  %s: ", prompt);
    if (scanf("%d", &v) != 1) v = 0;
    clear_line();
    return v;
}

/* ---------- commands ---------- */

static void cmd_add(void) {
    if (hand_count >= MAX_HANDS) {
        printf("  Hand limit reached (%d).\n", MAX_HANDS);
        return;
    }
    PokerHand *h = &hands[hand_count];
    memset(h, 0, sizeof(*h));
    h->id = hand_count + 1;

    // auto-fill date
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    snprintf(h->date, sizeof(h->date), "%04d-%02d-%02d %02d:%02d",
             t->tm_year + 1900, t->tm_mon + 1, t->tm_mday,
             t->tm_hour, t->tm_min);

    printf("\n  -- Add Hand #%d --\n", h->id);
    printf("  Date [%s]: ", h->date);
    {
        char tmp[64];
        if (fgets(tmp, sizeof(tmp), stdin) && tmp[0] != '\n') {
            tmp[strcspn(tmp, "\n")] = '\0';
            snprintf(h->date, sizeof(h->date), "%s", tmp);
        }
    }

    read_string("Table name",       h->table_name, sizeof(h->table_name));
    read_string("Hole cards (e.g. AhKs)", h->hole_cards, sizeof(h->hole_cards));
    read_string("Board (e.g. Qh9d3cTh2s)", h->board, sizeof(h->board));
    read_string("Hand type (e.g. Flush)", h->hand_type, sizeof(h->hand_type));
    h->num_players = read_int("Number of players");
    h->pot_size    = read_double("Pot size");
    h->coin_in     = read_double("Coins wagered (in)");
    h->coin_out    = read_double("Coins received (out)");

    char res[16];
    read_string("Result (win/loss/fold/split)", res, sizeof(res));
    h->result = parse_result(res);

    hand_count++;
    printf("  Hand #%d recorded.\n\n", h->id);
}

static void print_hand(const PokerHand *h) {
    printf("  %-4d | %-16s | %-12s | %-6s | %-14s | %-14s | %2d | %10.2f | %10.2f | %10.2f | %-5s\n",
           h->id, h->date, h->table_name, h->hole_cards, h->board,
           h->hand_type, h->num_players, h->pot_size,
           h->coin_in, h->coin_out, result_str(h->result));
}

static void print_header(void) {
    printf("  %-4s | %-16s | %-12s | %-6s | %-14s | %-14s | %2s | %10s | %10s | %10s | %-5s\n",
           "ID", "Date", "Table", "Cards", "Board", "Hand",
           "Pl", "Pot", "Coin In", "Coin Out", "Result");
    printf("  ");
    for (int i = 0; i < 130; i++) putchar('-');
    putchar('\n');
}

static void cmd_list(void) {
    if (hand_count == 0) {
        printf("\n  No hands recorded yet.\n\n");
        return;
    }
    printf("\n");
    print_header();
    for (int i = 0; i < hand_count; i++)
        print_hand(&hands[i]);
    printf("\n");
}

static void cmd_stats(void) {
    if (hand_count == 0) {
        printf("\n  No hands to summarise.\n\n");
        return;
    }
    int wins = 0, losses = 0, folds = 0, splits = 0;
    double total_in = 0, total_out = 0, biggest_pot = 0;

    for (int i = 0; i < hand_count; i++) {
        const PokerHand *h = &hands[i];
        switch (h->result) {
            case RESULT_WIN:   wins++;   break;
            case RESULT_LOSS:  losses++; break;
            case RESULT_FOLD:  folds++;  break;
            case RESULT_SPLIT: splits++; break;
        }
        total_in  += h->coin_in;
        total_out += h->coin_out;
        if (h->pot_size > biggest_pot) biggest_pot = h->pot_size;
    }
    double net = total_out - total_in;

    printf("\n  === Session Statistics ===\n");
    printf("  Hands played : %d\n", hand_count);
    printf("  Wins         : %d (%.1f%%)\n", wins,   100.0 * wins   / hand_count);
    printf("  Losses       : %d (%.1f%%)\n", losses, 100.0 * losses / hand_count);
    printf("  Folds        : %d (%.1f%%)\n", folds,  100.0 * folds  / hand_count);
    printf("  Splits       : %d (%.1f%%)\n", splits, 100.0 * splits / hand_count);
    printf("  Total coin in  : %.2f\n", total_in);
    printf("  Total coin out : %.2f\n", total_out);
    printf("  Net profit     : %.2f\n", net);
    printf("  Biggest pot    : %.2f\n", biggest_pot);
    printf("  =========================\n\n");
}

static void cmd_delete(void) {
    int id = read_int("Enter hand ID to delete");
    if (id < 1 || id > hand_count) {
        printf("  Invalid ID.\n");
        return;
    }
    int idx = id - 1;
    memmove(&hands[idx], &hands[idx + 1],
            (hand_count - idx - 1) * sizeof(PokerHand));
    hand_count--;
    // re-number
    for (int i = 0; i < hand_count; i++)
        hands[i].id = i + 1;
    printf("  Hand deleted. %d hand(s) remaining.\n", hand_count);
}

static void cmd_search(void) {
    char query[64];
    read_string("Search (table, cards, or hand type)", query, sizeof(query));
    int found = 0;
    printf("\n");
    print_header();
    for (int i = 0; i < hand_count; i++) {
        const PokerHand *h = &hands[i];
        if (strstr(h->table_name, query) ||
            strstr(h->hole_cards, query) ||
            strstr(h->board, query)      ||
            strstr(h->hand_type, query)) {
            print_hand(h);
            found++;
        }
    }
    if (!found) printf("  No matching hands.\n");
    printf("\n");
}

static void cmd_export_csv(void) {
    const char *csv = "poker_hands.csv";
    FILE *fp = fopen(csv, "w");
    if (!fp) { perror("export"); return; }
    fprintf(fp, "ID,Date,Table,HoleCards,Board,HandType,Players,Pot,CoinIn,CoinOut,Result\n");
    for (int i = 0; i < hand_count; i++) {
        const PokerHand *h = &hands[i];
        fprintf(fp, "%d,%s,%s,%s,%s,%s,%d,%.2f,%.2f,%.2f,%s\n",
                h->id, h->date, h->table_name, h->hole_cards, h->board,
                h->hand_type, h->num_players, h->pot_size,
                h->coin_in, h->coin_out, result_str(h->result));
    }
    fclose(fp);
    printf("  Exported %d hand(s) to %s\n", hand_count, csv);
}

/* ---------- main ---------- */

int main(void) {
    printf("\n");
    printf("  ========================================\n");
    printf("    CoinPoker Hand Tracker  v1.0\n");
    printf("  ========================================\n\n");

    load_hands();

    for (;;) {
        printf("  [A]dd hand  [L]ist  [S]tats  [D]elete  [F]ind  [E]xport CSV  [Q]uit\n");
        printf("  > ");
        char choice[8];
        if (!fgets(choice, sizeof(choice), stdin)) break;

        switch (choice[0]) {
            case 'a': case 'A': cmd_add();        break;
            case 'l': case 'L': cmd_list();       break;
            case 's': case 'S': cmd_stats();      break;
            case 'd': case 'D': cmd_delete();     break;
            case 'f': case 'F': cmd_search();     break;
            case 'e': case 'E': cmd_export_csv(); break;
            case 'q': case 'Q':
                save_hands();
                printf("  Goodbye!\n\n");
                return 0;
            default:
                printf("  Unknown option.\n");
        }
    }
    return 0;
}
