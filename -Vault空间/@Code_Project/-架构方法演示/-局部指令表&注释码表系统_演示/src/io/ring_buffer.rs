// =============================================================================
// ring_buffer.rs — Lock-Free 环形缓冲区
// =============================================================================

// >v<➰环形缓冲区 - SPSC Lock-Free实现 - 读写各一个线程，禁止多写
// 容量必须是 2 的幂，方便位运算取模
pub struct RingBuffer<T, const N: usize> {
    buf: [Option<T>; N],
    head: AtomicUsize,
    tail: AtomicUsize,
}

impl<T: Copy, const N: usize> RingBuffer<T, N> {
    pub fn push(&self, item: T) -> bool {
        let tail = self.tail.load(Ordering::Relaxed);
        let next = (tail + 1) & (N - 1);
        if next == self.head.load(Ordering::Acquire) {
            return false; // 满
        }
        unsafe { *self.buf[tail].get() = Some(item); }
        self.tail.store(next, Ordering::Release);
        true
    }
}
