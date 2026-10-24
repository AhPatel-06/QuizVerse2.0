#include <iostream>
#include <vector>
#include <iomanip>
using namespace std;

/*
 * QuizVerse C++ scoring module.
 * Input format:
 *   number_of_questions
 *   correct_answer_index user_answer_index
 *   ...
 * Indexes are zero-based. Use -1 for unanswered.
 * This standalone module demonstrates score computation in C++.
 */
int main() {
    int n;
    if (!(cin >> n) || n <= 0 || n > 500) {
        cerr << "Invalid question count\n";
        return 1;
    }
    int correct = 0;
    for (int i = 0; i < n; ++i) {
        int expected, selected;
        if (!(cin >> expected >> selected)) {
            cerr << "Invalid answer data\n";
            return 1;
        }
        if (selected == expected) ++correct;
    }
    double percentage = 100.0 * correct / n;
    cout << "Correct: " << correct << "/" << n << "\n";
    cout << "Percentage: " << fixed << setprecision(2) << percentage << "%\n";
    cout << "Result: " << (percentage >= 40.0 ? "PASS" : "KEEP PRACTISING") << "\n";
    return 0;
}