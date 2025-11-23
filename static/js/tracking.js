$(document).ready(function() {
    // Función para mostrar mensaje de error
    function showError(message) {
        $('#trackingContent').html(`
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-circle mr-2"></i>${message}
            </div>
        `);
        $('#trackingModal').modal('show');
    }

    // Función para mostrar los detalles del envío
    function showShipmentDetails(shipment) {
        const statusClass = {
            'pending': 'warning',
            'in_transit': 'info',
            'delivered': 'success',
            'cancelled': 'danger'
        }[shipment.status] || 'secondary';

        $('#trackingContent').html(`
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title mb-4">Detalles del Envío</h5>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Número de Seguimiento:</strong></p>
                            <p>${shipment.tracking_id}</p>
                        </div>
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Estado:</strong></p>
                            <span class="badge badge-${statusClass}">${shipment.status}</span>
                        </div>
                    </div>
                    <div class="row mb-3">
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Origen:</strong></p>
                            <p>${shipment.origin}</p>
                        </div>
                        <div class="col-md-6">
                            <p class="mb-1"><strong>Destino:</strong></p>
                            <p>${shipment.destination}</p>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12">
                            <p class="mb-1"><strong>Última Actualización:</strong></p>
                            <p>${shipment.last_update}</p>
                        </div>
                    </div>
                </div>
            </div>
        `);
        $('#trackingModal').modal('show');
    }

    // Manejar el clic en el botón de tracking
    $('#trackButton').click(function() {
        const trackingId = $('#trackingInput').val().trim();
        
        if (!trackingId) {
            showError('Por favor, ingrese un número de seguimiento');
            return;
        }

        // Mostrar indicador de carga
        $('#trackingContent').html(`
            <div class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="sr-only">Cargando...</span>
                </div>
                <p class="mt-2">Buscando información del envío...</p>
            </div>
        `);
        $('#trackingModal').modal('show');

        // Realizar la petición al servidor usando la ruta correcta
        $.get('./tracking.php', { tracking_id: trackingId })
            .done(function(response) {
                if (response.success) {
                    showShipmentDetails(response.data);
                } else if (response.error === 'not_found') {
                    showError('Envío no encontrado. Por favor, compruebe su número de seguimiento.');
                } else {
                    showError(response.message || 'Error al buscar el envío');
                }
            })
            .fail(function(jqXHR, textStatus, errorThrown) {
                console.error('Error:', textStatus, errorThrown);
                showError('Error al conectar con el servidor. Por favor, intente nuevamente.');
            });
    });

    // Permitir buscar al presionar Enter
    $('#trackingInput').keypress(function(e) {
        if (e.which === 13) {
            $('#trackButton').click();
        }
    });
}); 