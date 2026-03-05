import { LightningElement, api } from "lwc";
export default class CxInCustomGuidanceCenterIcon extends LightningElement {
  @api iconName;
  @api isComplete;

  @api markComplete() {
    this.isComplete = true;
  }

  get isVideo() {
    return this.iconN