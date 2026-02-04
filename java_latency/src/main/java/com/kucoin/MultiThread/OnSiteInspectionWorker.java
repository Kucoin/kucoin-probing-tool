package com.kucoin.MultiThread;


import com.kucoin.excutor.OnSiteInspectionTask;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
* @Author yomi
* @created at 2024/11/01/17:04
* @Version 1.0.0
* @Description 巡检探测worker
*/
public class OnSiteInspectionWorker {

    /***
     *  todo work交互的方案
     *  todo 首先实现 API + 现货 + btc币种的
     * @param args
     */
    public static void main(String[] args) {
        System.out.println("111");
        ArrayBlockingQueue<Runnable> workQueue = new ArrayBlockingQueue<>(100);
        ThreadPoolExecutor executor = new ThreadPoolExecutor(1, 10, 1, TimeUnit.HOURS, workQueue);

        for (int i = 0; i < 1; i++) {
            final int taskId = i;
            executor.execute(new OnSiteInspectionTask());
            System.out.println("Executing task " + taskId);
        }
        System.out.println("线程执行结束");
    }


}
