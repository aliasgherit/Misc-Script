import time
import platform

def my_test_function():
    # Example workload (you can replace this with your real code)
    total = 0
    for i in range(1, 1000000000):
        total += i
    return total

if __name__ == "__main__":
    print(f"Running on: {platform.system()} {platform.release()}")

    start_time = time.perf_counter()  # High-precision timer
    result = my_test_function()
    end_time = time.perf_counter()

    execution_time = end_time - start_time
    print(f"Result: {result}")
    print(f"Execution Time: {execution_time:.6f} seconds")
