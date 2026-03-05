/*
 * Copyright (c) 2020, salesforce.com, inc.
 * All rights reserved.
 * SPDX-License-Identifier: BSD-3-Clause
 * For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
 */


/**
 * @author Paul Lucas
 * @company       Salesforce
 *
 * @date 22/12/2023
 *
 * TODO:
 */

public abstract class XDO_Tool_QueueableBase implements System.Queueable {
    public static final Integer BATCH_SIZE_DEFAULT = 50;
    public static final Integer BATCH_SIZE_MIN = 1;
    public static final Integer BATCH_SIZE_MAX = 99;
    public static final Integer QUEUEABLE_DEPTH_DEFAULT = 5;

    protected XDO_Tool_IQueueableService service;

    protected Integer queueableDepth {
        get;
        set {
            this.queueableDepth = value == null ?
                    QUEUEABLE_DEPTH_DEFAULT :
                    Math.abs(value);
        }
    }

    protected Integer batchSize {
        get;
        set {
            this.batchSize = (value == null ||
                    value < BATCH_SIZE_MIN ||
                    value > BATCH_SIZE_MAX) ?
                    BATCH_SIZE_DEFAULT :
                    value;
        }
    }

    protected xDO_Tool_TrackingEventJob__mdt config {
        get;
        set {
            this.config = value;
        }
    }


    protected XDO_Tool_QueueableBase() {
        this.batchSize = BATCH_SIZE_DEFAULT;
        this.queueableDepth = QUEUEABLE_DEPTH_DEFAULT;
    }

    public interface XDO_Tool_IQueueableService {
    }

    public abstract void execute(System.QueueableContext context);
    public abstract XDO_Tool_QueueableBase setService(XDO_Tool_IQueueableService service);

    protected virtual XDO_Tool_QueueableBase getQueueableInstance() {
        return this;
    }

    public XDO_Tool_QueueableBase setBatchSize(Integer batchSize) {
        this.batchSize = batchSize;

        return this;
    }

    public XDO_Tool_QueueableBase setQueueableDepth(Integer queueableDepth) {
        this.queueableDepth = queueableDepth;

        return this;
    }

    public XDO_Tool_QueueableBase setConfig(xDO_Tool_TrackingEventJob__mdt config) {
        this.config = config;

        return this;
    }

    public void queue() {
        AsyncOptions options = new AsyncOptions();
        options.MaximumQueueableStackDepth = this.queueableDepth;

        System.enqueueJob(this.getQueueableInstance(), options);
    }

    protected void reQueueJob() {
        if (this.shouldChainQueueable()) {
            System.enqueueJob(this.getQueueableInstance());
        }
    }

    protected virtual Boolean shouldChainQueueable() {
        Boolean isWithinQueueableStackDepth = AsyncInfo.hasMaxStackDepth() ?
                AsyncInfo.getCurrentQueueableStackDepth() < AsyncInfo.getMaximumQueueableStackDepth() :
                true;

        return !Test.isRunningTest() &&
                Limits.getQueueableJobs() < Limits.getLimitQueueableJobs() &&
                isWithinQueueableStackDepth;
    }
}