import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ProcessPaymentComponent } from './process-payment.component';

describe('ProcessPaymentComponent', () => {
  let component: ProcessPaymentComponent;
  let fixture: ComponentFixture<ProcessPaymentComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ProcessPaymentComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(ProcessPaymentComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
