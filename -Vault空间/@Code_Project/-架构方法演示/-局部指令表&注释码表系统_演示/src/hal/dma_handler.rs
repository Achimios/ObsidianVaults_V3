// =============================================================================
// dma_handler.rs — DMA 中断处理
// =============================================================================

// >v<⚡中断处理 - DMA完成中断 - 此处绝对不能有 alloc/blocking call
#[interrupt]
fn DMA1_STREAM0() {
    // 向 ring_buffer push，不阻塞
    if let Some(data) = dma_read_complete() {
        SENSOR_BUF.push(data); // >v<➰环形缓冲区 复用
    }
    clear_dma_flag();
}
