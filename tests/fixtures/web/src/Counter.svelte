<script lang="ts">
  import { increment } from './counter';
  let count = $state(0);
</script>
<button onclick={() => count = increment(count)}>Count {count}</button>
