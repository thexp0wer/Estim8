"""
This is a temporary file to fix the ReferenceRatioForm and DisciplineReferenceRatioForm 
validation methods in forms.py
"""

# Fixed validation methods
def fixed_validation_ratio():
    # For ReferenceRatioForm
    def validate_high_ratio_reference(self, high_ratio):
        if self.low_ratio.data is not None and self.avg_ratio.data is not None and self.low_ratio.data > self.avg_ratio.data:
            raise ValidationError('Low ratio must be less than or equal to average ratio')
        if self.avg_ratio.data is not None and high_ratio.data is not None and self.avg_ratio.data > high_ratio.data:
            raise ValidationError('Average ratio must be less than or equal to high ratio')
    
    # For DisciplineReferenceRatioForm
    def validate_high_ratio_discipline(self, high_ratio):
        if self.low_ratio.data is not None and self.avg_ratio.data is not None and self.low_ratio.data > self.avg_ratio.data:
            raise ValidationError('Low ratio must be less than or equal to average ratio')
        if self.avg_ratio.data is not None and high_ratio.data is not None and self.avg_ratio.data > high_ratio.data:
            raise ValidationError('Average ratio must be less than or equal to high ratio')
    
    return validate_high_ratio_reference, validate_high_ratio_discipline