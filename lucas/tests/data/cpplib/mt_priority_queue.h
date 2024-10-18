#pragma once

#include <queue>
#include <mutex>
#include <condition_variable>

template<typename T, typename Container = std::vector<T>, typename Compare = std::less<typename Container::value_type>>
class ThreadSafePriorityQueue {
private:
    std::priority_queue<T, Container, Compare> pq;
    mutable std::mutex mutex;
    std::condition_variable cond;

public:
    void push(T value) {
        std::lock_guard<std::mutex> lock(mutex);
        pq.push(std::move(value));
        cond.notify_one();
    }

    T pop() {
        std::unique_lock<std::mutex> lock(mutex);
        cond.wait(lock, [this] { return !pq.empty(); });
        T value = std::move(pq.top());
        pq.pop();
        return value;
    }

    bool empty() const {
        std::lock_guard<std::mutex> lock(mutex);
        return pq.empty();
    }

    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex);
        return pq.size();
    }

    const T& top() const {
        std::lock_guard<std::mutex> lock(mutex);
        return pq.top();
    }
};
